from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from database.models import User, Client, Campaign, CampaignData, APIConnection, Alert, Report


# ── Users ──────────────────────────────────────────────────────────────────────
def create_user(db: Session, email: str, password_hash: str, full_name: str = None, agency_name: str = None) -> User:
    try:
        user = User(email=email, password_hash=password_hash, full_name=full_name, agency_name=agency_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError(f"User with email {email} already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error creating user: {str(e)}")


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    try:
        return db.query(User).filter(User.email == email).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error fetching user: {str(e)}")


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    try:
        user = get_user_by_id(db, user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error updating user: {str(e)}")


# ── Clients ────────────────────────────────────────────────────────────────────
def create_client(
    db: Session, user_id: int, name: str, 
    industry: str = None, target_cpl: float = None, monthly_budget: float = None
) -> Client:
    try:
        client = Client(
            user_id=user_id, name=name, industry=industry,
            target_cpl=target_cpl, monthly_budget=monthly_budget
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Client '{name}' already exists for this user")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error creating client: {str(e)}")


def get_clients_by_user(db: Session, user_id: int, active_only: bool = True) -> List[Client]:
    try:
        query = db.query(Client).filter(Client.user_id == user_id)
        if active_only:
            query = query.filter(Client.is_active == True)
        return query.order_by(Client.name).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error fetching clients: {str(e)}")


def get_client_by_id(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def update_client(db: Session, client_id: int, **kwargs) -> Optional[Client]:
    try:
        client = get_client_by_id(db, client_id)
        if client:
            for key, value in kwargs.items():
                if hasattr(client, key):
                    setattr(client, key, value)
            db.commit()
            db.refresh(client)
        return client
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error updating client: {str(e)}")


def delete_client(db: Session, client_id: int) -> bool:
    client = get_client_by_id(db, client_id)
    if client:
        client.is_active = False
        db.commit()
        return True
    return False


# ── Campaigns ──────────────────────────────────────────────────────────────────
def create_campaign(
    db: Session, client_id: int, campaign_name: str,
    platform: str = "manual", platform_campaign_id: str = None
) -> Campaign:
    try:
        campaign = Campaign(
            client_id=client_id, campaign_name=campaign_name,
            platform=platform, platform_campaign_id=platform_campaign_id
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error creating campaign: {str(e)}")


def get_campaigns_by_client(db: Session, client_id: int, active_only: bool = True) -> List[Campaign]:
    query = db.query(Campaign).filter(Campaign.client_id == client_id)
    if active_only:
        query = query.filter(Campaign.is_active == True)
    return query.order_by(Campaign.campaign_name).all()


def get_campaign_by_id(db: Session, campaign_id: int) -> Optional[Campaign]:
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


# ── Campaign Data ──────────────────────────────────────────────────────────────
def upsert_campaign_data(db: Session, campaign_id: int, date: date, **metrics) -> CampaignData:
    """Insert or update campaign data for a specific date"""
    try:
        data = db.query(CampaignData).filter(
            and_(CampaignData.campaign_id == campaign_id, CampaignData.date == date)
        ).first()
        
        if data:
            for key, value in metrics.items():
                if hasattr(data, key):
                    setattr(data, key, value)
        else:
            data = CampaignData(campaign_id=campaign_id, date=date, **metrics)
            db.add(data)
        
        db.commit()
        db.refresh(data)
        return data
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error upserting campaign data: {str(e)}")


def get_campaign_data(
    db: Session, campaign_id: int,
    start_date: date = None, end_date: date = None
) -> List[CampaignData]:
    try:
        query = db.query(CampaignData).filter(CampaignData.campaign_id == campaign_id)
        if start_date:
            query = query.filter(CampaignData.date >= start_date)
        if end_date:
            query = query.filter(CampaignData.date <= end_date)
        return query.order_by(CampaignData.date).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error fetching campaign data: {str(e)}")


def get_client_data_summary(
    db: Session, client_id: int,
    start_date: date = None, end_date: date = None
) -> List[CampaignData]:
    """Get all campaign data for a client within date range"""
    query = db.query(CampaignData).join(Campaign).filter(Campaign.client_id == client_id)
    if start_date:
        query = query.filter(CampaignData.date >= start_date)
    if end_date:
        query = query.filter(CampaignData.date <= end_date)
    return query.order_by(CampaignData.date).all()


# ── API Connections ────────────────────────────────────────────────────────────
def upsert_api_connection(
    db: Session, user_id: int, platform: str,
    access_token: str = None, refresh_token: str = None,
    token_expires_at: datetime = None, account_id: str = None
) -> APIConnection:
    try:
        conn = db.query(APIConnection).filter(
            and_(APIConnection.user_id == user_id, APIConnection.platform == platform)
        ).first()
        
        if conn:
            if access_token:
                conn.access_token = access_token
            if refresh_token:
                conn.refresh_token = refresh_token
            if token_expires_at:
                conn.token_expires_at = token_expires_at
            if account_id:
                conn.account_id = account_id
            conn.is_active = True
        else:
            conn = APIConnection(
                user_id=user_id, platform=platform,
                access_token=access_token, refresh_token=refresh_token,
                token_expires_at=token_expires_at, account_id=account_id
            )
            db.add(conn)
        
        db.commit()
        db.refresh(conn)
        return conn
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error upserting API connection: {str(e)}")


def get_api_connections(db: Session, user_id: int) -> List[APIConnection]:
    return db.query(APIConnection).filter(
        and_(APIConnection.user_id == user_id, APIConnection.is_active == True)
    ).all()


def update_last_sync(db: Session, connection_id: int):
    conn = db.query(APIConnection).filter(APIConnection.id == connection_id).first()
    if conn:
        conn.last_sync_at = datetime.utcnow()
        db.commit()


# ── Alerts ─────────────────────────────────────────────────────────────────────
def create_alert(
    db: Session, client_id: int, alert_type: str, severity: str, message: str,
    campaign_id: int = None, metric_value: float = None, threshold_value: float = None
) -> Alert:
    try:
        alert = Alert(
            client_id=client_id, campaign_id=campaign_id,
            alert_type=alert_type, severity=severity, message=message,
            metric_value=metric_value, threshold_value=threshold_value
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error creating alert: {str(e)}")


def get_alerts(
    db: Session, client_id: int = None, user_id: int = None,
    unread_only: bool = False, limit: int = 50
) -> List[Alert]:
    query = db.query(Alert)
    
    if client_id:
        query = query.filter(Alert.client_id == client_id)
    elif user_id:
        query = query.join(Client).filter(Client.user_id == user_id)
    
    if unread_only:
        query = query.filter(Alert.is_read == False)
    
    return query.order_by(desc(Alert.created_at)).limit(limit).all()


def mark_alert_read(db: Session, alert_id: int):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_read = True
        db.commit()


# ── Reports ────────────────────────────────────────────────────────────────────
def create_report(
    db: Session, client_id: int, report_type: str,
    date_range_start: date, date_range_end: date, pdf_path: str
) -> Report:
    try:
        report = Report(
            client_id=client_id, report_type=report_type,
            date_range_start=date_range_start, date_range_end=date_range_end,
            pdf_path=pdf_path
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error creating report: {str(e)}")


def get_reports(db: Session, client_id: int, limit: int = 20) -> List[Report]:
    return db.query(Report).filter(Report.client_id == client_id)\
        .order_by(desc(Report.generated_at)).limit(limit).all()


def mark_report_sent(db: Session, report_id: int):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        report.sent_at = datetime.utcnow()
        db.commit()
