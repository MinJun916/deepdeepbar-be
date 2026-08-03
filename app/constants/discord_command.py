ORDER_MODE_COMMAND_NAME = "주문모드"
ORDER_MODE_OPTION_NAME = "모드"
ORDER_MODE_ENABLED_VALUE = "ordering"
ORDER_MODE_MENU_ONLY_VALUE = "menu_only"

ORDER_MODE_VALUE_TO_ENABLED = {
    ORDER_MODE_ENABLED_VALUE: True,
    ORDER_MODE_MENU_ONLY_VALUE: False,
}


def build_order_mode_command_payload() -> dict:
    return {
        "name": ORDER_MODE_COMMAND_NAME,
        "description": "매장의 주문 가능 여부를 변경합니다.",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": ORDER_MODE_OPTION_NAME,
                "description": "적용할 주문 모드를 선택합니다.",
                "required": True,
                "choices": [
                    {
                        "name": "주문 가능",
                        "value": ORDER_MODE_ENABLED_VALUE,
                    },
                    {
                        "name": "메뉴판 전용",
                        "value": ORDER_MODE_MENU_ONLY_VALUE,
                    },
                ],
            }
        ],
    }
