import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.auth.user_utils import sign_up_or_login_user, create_initial_user


class TestSignupOrLoginUser:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.PK_ENV = "dev"
        mock_env.LOGIN_CODE_EXPIRY = 15
        return mock_env

    @pytest.fixture
    def db(self):
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.get_collection.return_value = mock_collection
        return mock_db

    @pytest.fixture
    def email_manager(self):
        return MagicMock()

    @pytest.fixture
    def logger(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_existing_user_no_email(self, env, db, email_manager, logger):
        user = {"id": "user1", "email": "test@example.com"}
        db.get_collection.return_value.find_one = AsyncMock(return_value=user)
        db.get_collection.return_value.update_one = AsyncMock()
        with patch("app.modules.auth.user_utils.get_login_code") as mock_get_login_code:
            mock_get_login_code.return_value = MagicMock(
                hashed_login_code="hash",
                salt="salt",
                expiry="expiry",
                login_code="code",
            )
            result = await sign_up_or_login_user(
                "test@example.com", False, env, db, email_manager, logger
            )
            assert result == "code"
            email_manager.send_signup_notification.assert_not_called()
            email_manager.send_login_code.assert_not_called()
            db.get_collection.return_value.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_new_user_with_email(self, env, db, email_manager, logger):
        db.get_collection.return_value.find_one = AsyncMock(return_value=None)
        db.get_collection.return_value.update_one = AsyncMock()
        with patch(
            "app.modules.auth.user_utils.create_initial_user", new_callable=AsyncMock
        ) as mock_create_initial_user:
            mock_create_initial_user.return_value = {
                "id": "user2",
                "email": "new@example.com",
            }
            with patch(
                "app.modules.auth.user_utils.get_login_code"
            ) as mock_get_login_code:
                mock_get_login_code.return_value = MagicMock(
                    hashed_login_code="hash",
                    salt="salt",
                    expiry="expiry",
                    login_code="code",
                )
                result = await sign_up_or_login_user(
                    "new@example.com", True, env, db, email_manager, logger
                )
                assert result == "code"
                email_manager.send_signup_notification.assert_called_once_with(
                    "new@example.com"
                )
                email_manager.send_login_code.assert_called_once_with(
                    "new@example.com", "code"
                )
                db.get_collection.return_value.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_new_user_no_email_manager(self, env, db, logger):
        db.get_collection.return_value.find_one = AsyncMock(return_value=None)
        db.get_collection.return_value.update_one = AsyncMock()
        with patch(
            "app.modules.auth.user_utils.create_initial_user", new_callable=AsyncMock
        ) as mock_create_initial_user:
            mock_create_initial_user.return_value = {
                "id": "user3",
                "email": "noemail@example.com",
            }
            with patch(
                "app.modules.auth.user_utils.get_login_code"
            ) as mock_get_login_code:
                mock_get_login_code.return_value = MagicMock(
                    hashed_login_code="hash",
                    salt="salt",
                    expiry="expiry",
                    login_code="code",
                )
                result = await sign_up_or_login_user(
                    "noemail@example.com", True, env, db, None, logger
                )
                assert result == "code"

    @pytest.mark.asyncio
    async def test_no_email_sent_in_test_env(self, db, email_manager, logger):
        env = MagicMock()
        env.PK_ENV = "test"
        env.LOGIN_CODE_EXPIRY = 15
        db.get_collection.return_value.find_one = AsyncMock(return_value=None)
        db.get_collection.return_value.update_one = AsyncMock()
        with patch(
            "app.modules.auth.user_utils.create_initial_user", new_callable=AsyncMock
        ) as mock_create_initial_user:
            mock_create_initial_user.return_value = {
                "id": "user4",
                "email": "testenv@example.com",
            }
            with patch(
                "app.modules.auth.user_utils.get_login_code"
            ) as mock_get_login_code:
                mock_get_login_code.return_value = MagicMock(
                    hashed_login_code="hash",
                    salt="salt",
                    expiry="expiry",
                    login_code="code",
                )
                result = await sign_up_or_login_user(
                    "testenv@example.com", True, env, db, email_manager, logger
                )
                assert result == "code"
                email_manager.send_signup_notification.assert_not_called()
                email_manager.send_login_code.assert_not_called()


class TestCreateInitialUser:
    @pytest.fixture
    def db(self):
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.get_collection.return_value = mock_collection
        return mock_db

    @pytest.fixture
    def logger(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_create_initial_user_inserts_user(self, db, logger):
        email = "test@example.com"
        db.get_collection.return_value.insert_one = AsyncMock()
        user = await create_initial_user(email, db, logger)
        db.get_collection.return_value.insert_one.assert_awaited_once()
        assert user["email"] == email
        assert user["id"]
        assert user["created_at"]
        assert user["login_code_hash"] is None
        assert user["login_code_salt"] is None
        assert user["login_code_expires"] is None
        assert user["password_hash"] is None
        assert user["password_salt"] is None

    @pytest.mark.asyncio
    async def test_logger_called(self, db, logger):
        email = "logtest@example.com"
        db.get_collection.return_value.insert_one = AsyncMock()
        user = await create_initial_user(email, db, logger)
        logger.info.assert_called()
        logger.warning.assert_any_call(
            "Initial settings generation is not implemented yet."
        )
        logger.warning.assert_any_call(
            "Initial activities data generation is not implemented yet."
        )
