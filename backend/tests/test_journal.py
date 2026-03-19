from datetime import date

from app.schemas.journal import TradeJournalCreate
from app.services.auth_service import signup_user
from app.services.journal_service import create_journal



def test_journal_profit_calculation(db_session):
    user = signup_user(db_session, 'journal@example.com', 'password123', 'password123')

    journal = create_journal(
        db_session,
        user,
        TradeJournalCreate(
            strategy_id=None,
            stock_code='005930',
            stock_name='삼성전자',
            trade_date=date.today(),
            buy_reason='테스트',
            quantity=10,
            entry_price=100,
            exit_price=110,
            memo='memo',
        ),
    )

    assert float(journal.profit_value) == 100.0
    assert float(journal.profit_rate) == 0.1
