import pytest
from app.core import security
from app.workers import tasks
from app.models.retry_policy import RetryPolicy


def test_password_hashing():
    password = "super-secure-pass"
    hashed = security.get_password_hash(password)
    assert hashed != password
    assert security.verify_password(password, hashed)
    assert not security.verify_password("wrong-pass", hashed)


def test_token_creation_and_validation():
    subject = "test-user-id"
    token = security.create_access_token(subject)
    assert isinstance(token, str)
    
    # Decode token
    from jose import jwt
    payload = jwt.decode(token, security.settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    assert payload.get("sub") == subject


def test_retry_delay_calculations():
    # Fixed Delay Strategy
    policy_fixed = RetryPolicy(strategy="fixed", base_delay=10, backoff_factor=2)
    assert tasks.calculate_retry_delay(1, policy_fixed) == 10
    assert tasks.calculate_retry_delay(2, policy_fixed) == 10

    # Linear Backoff Strategy
    policy_linear = RetryPolicy(strategy="linear", base_delay=5, backoff_factor=2)
    assert tasks.calculate_retry_delay(1, policy_linear) == 5
    assert tasks.calculate_retry_delay(2, policy_linear) == 10
    assert tasks.calculate_retry_delay(3, policy_linear) == 15

    # Exponential Backoff Strategy
    policy_exp = RetryPolicy(strategy="exponential", base_delay=5, backoff_factor=2)
    assert tasks.calculate_retry_delay(1, policy_exp) == 5       # 5 * (2 ** 0)
    assert tasks.calculate_retry_delay(2, policy_exp) == 10      # 5 * (2 ** 1)
    assert tasks.calculate_retry_delay(3, policy_exp) == 20      # 5 * (2 ** 2)
