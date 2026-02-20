from src.repositories.author import AuthorRepository
from src.repositories.book import BookRepository
from src.repositories.booking import BookingRepository
from src.repositories.exchange_point import ExchangePointRepository
from src.repositories.instance import InstanceRepository
from src.repositories.organisation import OrganisationRepository
from src.repositories.new_added_instance import NewAddedInstanceRepository
from src.repositories.user import UserRepository


class DBManager:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.user = UserRepository(self.session)
        self.book = BookRepository(self.session)
        self.instance = InstanceRepository(self.session)
        self.author = AuthorRepository(self.session)
        self.exchange_point = ExchangePointRepository(self.session)
        self.organisation = OrganisationRepository(self.session)
        self.booking = BookingRepository(self.session)
        self.new_added_instance = NewAddedInstanceRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()
