from providers import Provider
from db.models import Ad, AdIsNotFound
from sqlalchemy.orm.session import Session as SQLASession


class AdIsUpdated:
    previous_version: Ad
    current_version: Ad

    def __init__(self, previous_version: Ad, current_version: Ad) -> None:
        self.previous_version = previous_version
        self.current_version = current_version

    def get_description(self, session: SQLASession):
        diff = self.previous_version.get_diff(self.current_version)
        base_string = f"""
        URL: {self.current_version.url}
        DIFF: {diff}
        HISTORY:
        """
        for attr in diff:
            history = self.current_version.get_attribute_history(session=session, attribute_name=attr)
            history = {k.date().strftime("%Y-%m-%d"): v for k,v in history.items()}
            base_string = f"{base_string}\t{attr}: {history}\n\t\t"
        return base_string


def fetch_and_save_to_db(session: SQLASession, provider: Provider) -> tuple[list[Ad], list[AdIsUpdated]]:
    ads_info = provider.get_ads()

    new_ads = []
    update_events = []

    for ad_info in ads_info:
        try:
            ad = Ad.most_recent_version(session=session, external_id=ad_info.id)
        except AdIsNotFound:
            new_ads.append(Ad.create(session=session, ad_info=ad_info))
            continue

        new_version = ad.add_version(session=session, ad_info=ad_info)
        if new_version:
            update_events.append(AdIsUpdated(previous_version=ad, current_version=new_version))

    session.commit()
    session.close()
    return new_ads, update_events
