# app/services/api_service.py

from .api_client import APIClient

class APIService:
    def __init__(self):
        self.client = APIClient()

    async def global_search(self, query):
        endpoint = f"v2/feed/global-search?q={query}"
        return await self.client.make_request(endpoint)

    async def get_item_view(self, item_id, branch_key):
        endpoint = f"v1/shopping-lists/item/{item_id}/view?branchKey={branch_key}"
        return await self.client.make_request(endpoint)

    async def get_shopping_lists(self, branch_key):
        endpoint = f"v3/shopping-lists?branchKey={branch_key}"
        return await self.client.make_request(endpoint)

    async def update_shopping_list(self, shopping_list_uid, item_uid, branch_uid, count, comment):
        endpoint = "v3/shopping-lists"
        data = {
            "shoppingListUid": shopping_list_uid,
            "itemUid": item_uid,
            "branchUid": branch_uid,
            "count": count,
            "comment": comment
        }
        return await self.client.make_request(endpoint, method="PUT", data=data)

    async def create_invoice(self, shopping_list_uid, address_uid):
        endpoint = f"v3/shopping-lists/{shopping_list_uid}/invoice"
        data = {
            "addressUid": address_uid,
            "deliveryType": "time_definite",
            "timeSlotUid": "",
            "deductFromBalance": False,
            "selectedWalletCredits": [],
        }
        return await self.client.make_request(endpoint, method="POST", data=data)

    async def place_order(self, shopping_list_uid, address_uid, tip=None):
        endpoint = "v3/orders"
        data = {
            "addressUid": address_uid,
            "timeSlotUid": "",
            "offCode": "",
            "shoppingListUid": shopping_list_uid,
            "tip": tip,
            "deliveryTimeType": "post",
            "deductFromBalance": False,
            "selectedWalletCredits": []
        }
        return await self.client.make_request(endpoint, method="POST", data=data)
