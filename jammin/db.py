import secrets
import asyncio
from pathlib import Path
import toml
from sqlalchemy_aio import ASYNCIO_STRATEGY
from sqlalchemy import (
    Column, Integer, Boolean, DateTime, ForeignKey, MetaData, Table, Text, create_engine, select, func)
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy.exc import IntegrityError


metadata = MetaData()


users = Table(
    'users', metadata,
    Column('nick', Text, primary_key=True),
    Column('token', Text),
    Column('score', Integer),
)


attempts = Table(
    'attempts', metadata,
    Column('id', Integer, primary_key=True),
    Column('challenge', Text),
    Column('user', None, ForeignKey('users.nick')),
    Column('timestamp', DateTime, default=func.now()),
    Column('succeeded', Boolean),
)


def _row_to_user(row):
    return {
        'nick': row[0],
        'token': row[1],
        'score': row[2],
    }


def _row_to_attempt(row):
    return {
        'id': row[0],
        'challenge': row[1],
        'user': row[2],
        'timestamp': row[3],
        'succeeded': row[4],
    }


def _parse_challenge_conf(conf_file):
    challenge = conf_file.parent.name

    try:
        conf = toml.loads(conf_file.read_text())
        conf['name'] = challenge
        try:
            conf['subject'] = (conf_file.parent / 'subject.md').read_text()
        except FileExistsError:
            conf['subject'] = ''

        conf['maxseed'] = conf.get('maxseed', 1000)
        if not isinstance(conf['maxseed'], int):
            raise ValueError('maxseed must be an integer')
        conf['interactive'] = conf.get('interactive', False)
        if not isinstance(conf['interactive'], bool):
            raise ValueError('interactive must be a boolean')
        conf['runner'] = Path(str(conf.get('runner', 'runner.py')))
        if conf['runner'].is_file():
            raise ValueError('runner must be a valid file')
        if 'solver' not in conf:
            conf['solver'] = None
        else:
            conf['solver'] = Path(str(conf.get['solver']))
            if conf['solver'].is_file():
                raise ValueError('solver must be a valid file')

    except Exception as exc:
        raise RuntimeError(f'Configuration error for challenge `{challenge}` : {exc}') from exc

    return conf


class DB:

    @classmethod
    async def init(cls, challenges_dir='.', dbfile='test.db'):
        engine = create_engine(
            f"sqlite:///{dbfile}", strategy=ASYNCIO_STRATEGY
        )
        challenges_dir = Path(challenges_dir)
        assert challenges_dir.is_dir()

        # Create the table
        await engine.execute(CreateTable(users))
        await engine.execute(CreateTable(attempts))
        conn = await engine.connect()

        return cls(challenges_dir, engine, conn)

    def __init__(self, challenges_dir, engine, conn):
        self.challenges_dir = challenges_dir
        self.engine = engine
        self.conn = conn

    def get_challenges(self):
        confs = []
        for conf_file in self.challenges_dir.glob('*/challenge.toml'):
            confs.append(_parse_challenge_conf(conf_file))
        return confs

    async def create_user(self, nick):
        token = secrets.token_hex(8)
        await self.conn.execute(users.insert().values(
            nick=nick, token=token, score=0
        ))
        return await self.get_user(nick)

    async def get_user(self, nick):
        result = await self.conn.execute(users.select().where(users.c.nick==nick))
        return _row_to_user(await result.fetchone())

    async def get_users(self):
        result = await self.conn.execute(users.select())
        return [_row_to_user(row) for row in await result.fetchall()]

    async def create_attempt(self, user, challenge, succeeded):
        ret = await self.conn.execute(attempts.insert().values(
            user=user, challenge=challenge, succeeded=succeeded
        ))

    async def get_user_attempts(self, nick):
        result = await self.conn.execute(attempts.select().where(attempts.c.user==nick))
        return [_row_to_attempt(row) for row in await result.fetchall()]

    async def get_challenge_attempts(self, challenge):
        result = await self.conn.execute(attempts.select().where(attempts.c.challenge==challenge))
        return [_row_to_attempt(row) for row in await result.fetchall()]
