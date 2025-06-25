from unittest.mock import AsyncMock, patch

from app.modules.reddit.reddit_types import RedditPost


class TestUpdateAndGetRedditConfig:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Getting initial config
        response = client.get(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sets" in data
        assert "blockedUsers" in data
        assert len(data["sets"]) == 1
        assert data["sets"][0]["name"] == "Default"
        assert data["sets"][0]["subs"] == []
        assert data["sets"][0]["usernames"] == []

        # Updating config
        update_data = {
            "sets": [
                {
                    "name": "set1",
                    "subs": ["funny", "programmerHumor"],
                    "usernames": ["alice"],
                }
            ],
            "blockedUsers": ["baduser"],
        }
        response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert "sets" in updated_data
        assert "blockedUsers" in updated_data
        assert len(updated_data["sets"]) == 1
        assert updated_data["sets"][0]["name"] == "set1"
        assert updated_data["sets"][0]["subs"] == ["funny", "programmerHumor"]
        assert updated_data["sets"][0]["usernames"] == ["alice"]
        assert updated_data["blockedUsers"] == ["baduser"]
        assert updated_data["id"] == data["id"]

        # Add more sets, usernames, and subs
        additional_update_data = {
            "sets": [
                {
                    "name": "set1",
                    "subs": ["funny", "programmerHumor"],
                    "usernames": ["alice", "charlie"],
                },
                {"name": "set2", "subs": ["aww"], "usernames": ["bob"]},
                {"name": "set3", "subs": ["gaming", "assassinsCreed"], "usernames": []},
            ],
            "blockedUsers": ["baduser", "troll"],
        }
        response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
            json=additional_update_data,
        )
        assert response.status_code == 200
        additional_updated_data = response.json()
        assert "sets" in additional_updated_data
        assert "blockedUsers" in additional_updated_data
        assert len(additional_updated_data["sets"]) == 3
        assert additional_updated_data["sets"][0]["name"] == "set1"
        assert additional_updated_data["sets"][0]["subs"] == [
            "funny",
            "programmerHumor",
        ]
        assert additional_updated_data["sets"][0]["usernames"] == ["alice", "charlie"]
        assert additional_updated_data["sets"][1]["name"] == "set2"
        assert additional_updated_data["sets"][1]["subs"] == ["aww"]
        assert additional_updated_data["sets"][1]["usernames"] == ["bob"]
        assert additional_updated_data["sets"][2]["name"] == "set3"
        assert additional_updated_data["sets"][2]["subs"] == [
            "gaming",
            "assassinsCreed",
        ]
        assert additional_updated_data["sets"][2]["usernames"] == []
        assert additional_updated_data["blockedUsers"] == ["baduser", "troll"]
        assert additional_updated_data["id"] == updated_data["id"]

        # Verify the final config
        response = client.get(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        final_data = response.json()
        assert "sets" in final_data
        assert "blockedUsers" in final_data
        assert len(final_data["sets"]) == 3
        assert final_data["sets"][0]["name"] == "set1"
        assert final_data["sets"][0]["subs"] == ["funny", "programmerHumor"]
        assert final_data["sets"][0]["usernames"] == ["alice", "charlie"]
        assert final_data["sets"][1]["name"] == "set2"
        assert final_data["sets"][1]["subs"] == ["aww"]
        assert final_data["sets"][1]["usernames"] == ["bob"]
        assert final_data["sets"][2]["name"] == "set3"
        assert final_data["sets"][2]["subs"] == ["gaming", "assassinsCreed"]
        assert final_data["sets"][2]["usernames"] == []
        assert final_data["blockedUsers"] == ["baduser", "troll"]

    def test_get_config_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to get config for a user without any Reddit config
        response = client.get(
            "/reddit/config",
            headers={"Authorization": f"Bearer wrong_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_update_config_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to update config with an invalid token
        update_data = {
            "sets": [
                {
                    "name": "set1",
                    "subs": ["funny", "programmerHumor"],
                    "usernames": ["alice"],
                }
            ],
            "blockedUsers": ["baduser"],
        }
        response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer wrong_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_update_config_invalid_data(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to update config with invalid data (missing required fields)
        invalid_update_data = {
            "sets": [
                {
                    "name": "set1",
                    "subs": ["funny", "programmerHumor"],
                }  # Missing 'usernames'
            ],
            "blockedUsers": ["baduser"],
        }
        response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
            json=invalid_update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "field required" in data["detail"][0]["msg"].lower()


class TestFetchSubRedditPosts:
    def test_fetch_sub_posts_multiple_subs(self, client, login_user):
        token, user_id, email = login_user

        fake_posts_funny = [
            {
                "title": "Funny Post",
                "url": "https://reddit.com/funny1",
                "author": "alice",
                "subreddit": "funny",
            }
        ]
        fake_posts_gaming = [
            {
                "title": "Gaming Post",
                "url": "https://reddit.com/gaming1",
                "author": "bob",
                "subreddit": "gaming",
            }
        ]
        with patch("app.modules.reddit.fetch_sub_posts.RedditApi") as mock_api:
            instance = mock_api.return_value
            instance.fetch_sub_posts = AsyncMock(
                side_effect=[fake_posts_funny, fake_posts_gaming]
            )
            instance.close = AsyncMock()
            response = client.post(
                "/reddit/subs",
                headers={"Authorization": f"Bearer {token}"},
                json={"subs": ["funny", "gaming"], "limit": 1},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["entities"]) == 2
            titles = [post["title"] for post in data["entities"]]
            assert "Funny Post" in titles
            assert "Gaming Post" in titles

    def test_fetch_sub_posts_with_blocked_users(self, client, login_user):
        token, user_id, email = login_user

        # Set up blocked users in the config
        update_data = {
            "sets": [],
            "blockedUsers": ["baduser", "troll"],
        }
        config_response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert config_response.status_code == 200

        fake_posts_funny = [
            RedditPost(
                title="Funny Post",
                url="https://reddit.com/funny1",
                author="alice",
                subreddit="funny",
            ),
            RedditPost(
                title="Bad Funny Post",
                url="https://reddit.com/funny2",
                author="baduser",
                subreddit="funny",
            ),
        ]
        fake_posts_gaming = [
            RedditPost(
                title="Bad Gaming Post",
                url="https://reddit.com/gaming1",
                author="troll",
                subreddit="gaming",
            ),
            RedditPost(
                title="Gaming Post",
                url="https://reddit.com/gaming2",
                author="bob",
                subreddit="gaming",
            ),
        ]
        with patch("app.modules.reddit.fetch_sub_posts.RedditApi") as mock_api:
            instance = mock_api.return_value
            instance.fetch_sub_posts = AsyncMock(
                side_effect=[fake_posts_funny, fake_posts_gaming]
            )
            instance.close = AsyncMock()
            response = client.post(
                "/reddit/subs",
                headers={"Authorization": f"Bearer {token}"},
                json={"subs": ["funny", "gaming"], "limit": 2},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["entities"]) == 2
            titles = [post["title"] for post in data["entities"]]
            assert "Funny Post" in titles
            assert "Gaming Post" in titles


class TestFetchUserRedditPosts:
    def test_fetch_user_posts_multiple_users(self, client, login_user):
        token, user_id, email = login_user

        fake_posts_alice = [
            {
                "title": "Alice's Post",
                "url": "https://reddit.com/alice1",
                "author": "alice",
                "subreddit": "funny",
            }
        ]
        fake_posts_bob = [
            {
                "title": "Bob's Post",
                "url": "https://reddit.com/bob1",
                "author": "bob",
                "subreddit": "gaming",
            }
        ]
        with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
            instance = mock_api.return_value
            instance.fetch_user_posts = AsyncMock(
                side_effect=[fake_posts_alice, fake_posts_bob]
            )
            instance.close = AsyncMock()
            response = client.post(
                "/reddit/users",
                headers={"Authorization": f"Bearer {token}"},
                json={"usernames": ["alice", "bob"], "limit": 1},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["entities"]) == 2
            titles = [post["title"] for post in data["entities"]]
            assert "Alice's Post" in titles
            assert "Bob's Post" in titles

    def test_fetch_sub_posts_with_blocked_users(self, client, login_user):
        token, user_id, email = login_user

        # Set up blocked users in the config
        update_data = {
            "sets": [],
            "blockedUsers": ["baduser", "troll"],
        }
        config_response = client.put(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert config_response.status_code == 200

        fake_posts_alice = [
            RedditPost(
                title="Funny Post",
                url="https://reddit.com/funny1",
                author="alice",
                subreddit="funny",
            ),
            RedditPost(
                title="Other Funny Post",
                url="https://reddit.com/funny2",
                author="alice",
                subreddit="funny",
            ),
        ]
        fake_posts_troll = [
            RedditPost(
                title="Bad Gaming Post",
                url="https://reddit.com/gaming1",
                author="troll",
                subreddit="gaming",
            ),
        ]
        with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
            instance = mock_api.return_value
            instance.fetch_user_posts = AsyncMock(
                side_effect=[fake_posts_alice, fake_posts_troll]
            )
            instance.close = AsyncMock()
            response = client.post(
                "/reddit/users",
                headers={"Authorization": f"Bearer {token}"},
                json={"usernames": ["alice", "troll"], "limit": 2},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["entities"]) == 2
            titles = [post["title"] for post in data["entities"]]
            assert "Funny Post" in titles
            assert "Other Funny Post" in titles
