from typing import Optional

from .api_client import APIClient


class APIService:
    """
    Thin, typed façade over the raw REST endpoints.
    """

    def __init__(self, client: Optional[APIClient] = None) -> None:
        self.client = client or APIClient()

    # ---------- catalogue -------------------------------------------------

    def global_search(self, query: str, *, token: str):
        return self.client.make_request(
            f"ai-assistance/items?q={query}", token=token
        )

    def get_item_view(self, item_id: str, branch_key: str, *, token: str):
        return self.client.make_request(
            f"cu/v1/shopping-lists/item/{item_id}/view?branchKey={branch_key}",
            token=token,
        )

    # ---------- shopping lists --------------------------------------------

    def get_shopping_lists(self, branch_key: str, *, token: str):
        return self.client.make_request(
            f"cu/v3/shopping-lists?branchKey={branch_key}", token=token
        )

    def update_shopping_list(
        self,
        shopping_list_uid: str,
        item_uid: str,
        branch_uid: str,
        count: int,
        comment: str,
        *,
        token: str,
    ):
        data = {
            "shoppingListUid": shopping_list_uid,
            "itemUid": item_uid,
            "branchUid": branch_uid,
            "count": count,
            "comment": comment,
        }
        return self.client.make_request(
            "cu/v3/shopping-lists", method="PUT", data=data, token=token
        )

    # ---------- checkout --------------------------------------------------

    def create_invoice(self, shopping_list_uid: str, address_uid: str, *, token: str):
        data = {
            "addressUid": address_uid,
            "deliveryType": "time_definite",
            "timeSlotUid": "",
            "deductFromBalance": False,
            "selectedWalletCredits": [],
        }
        return self.client.make_request(
            f"cu/v3/shopping-lists/{shopping_list_uid}/invoice",
            method="POST",
            data=data,
            token=token,
        )

    def place_order(
        self,
        shopping_list_uid: str,
        address_uid: str,
        tip: Optional[float] = None,
        *,
        token: str,
    ):
        data = {
            "addressUid": address_uid,
            "timeSlotUid": "",
            "offCode": "",
            "shoppingListUid": shopping_list_uid,
            "tip": tip,
            "deliveryTimeType": "post",
            "deductFromBalance": False,
            "selectedWalletCredits": [],
        }
        return self.client.make_request(
            "cu/v3/orders", method="POST", data=data, token=token
        )

    # ---------- user profile ----------------------------------------------

    def get_addresses(self, *, token: str):
        return self.client.make_request("cu/v1/addresses", token=token)

