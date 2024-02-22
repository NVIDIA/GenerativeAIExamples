# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from openai_function_calling import Function, Parameter


class Cart:
    """Shopping cart"""

    def __init__(self):
        self.items = {}

    def __str__(self) -> str:
        return str(self.items)

    def __repr__(self) -> str:
        return str(self.items)

    def reset(self):
        """Reset"""
        self.items = {}

    def view_cart(self) -> str:
        """View cart"""
        return f"The following items are in your cart: {str(self.items)}"

    def add_to_cart(self, name: str, quantity: int = 1) -> str:
        """Add to cart"""
        if name in self.items:
            self.items[name] = self.items[name] + quantity
            quantity = self.items[name]
        else:
            self.items[name] = quantity
        return f"{quantity} unit(s) of of {name} have been added to your cart."

    def remove_from_cart(self, name: str) -> str:
        """Remove from cart"""
        if name in self.items:
            self.items.pop(name, None)
            response = (
                f"{name} has been removed from your cart. You have no units remaining."
            )
        else:
            response = f"You don't have any units of {name} in your cart."

        return response

    def modify_item_in_cart(self, name: str, quantity: int) -> str:
        """Modify item in cart"""
        self.items[name] = quantity
        return f"You now have {quantity} unit(s) of of {name} in your cart."


view_cart_function = Function(
    name="view_cart",
    description="Show the customer all of the items in their shopping car",
    parameters=None,
    required_parameters=None,
)

add_to_cart_function = Function(
    name="add_to_cart",
    description="Add item to the customer's shopping cart",
    parameters=[
        Parameter(
            name="name",
            type="string",
            description="The name of the item to add to the customer's shopping cart",
        ),
        Parameter(
            name="quantity",
            type="integer",
            description="The quantity of that item to add to the customer's shopping cart",
        ),
    ],
    required_parameters=["name", "quantity"],
)

remove_from_cart_function = Function(
    name="remove_from_cart",
    description="Remove the item from the customer's shopping cart",
    parameters=[
        Parameter(
            name="name",
            type="string",
            description="The name of the item to remove from the customer's shopping cart",
        ),
    ],
    required_parameters=["name"],
)

modify_item_in_cart_function = Function(
    name="modify_item_in_cart",
    description="Update/modify the number of units of an item in a customer's shopping cart",
    parameters=[
        Parameter(
            name="name",
            type="string",
            description="The name of the item to update/modify in the customer's shopping cart",
        ),
        Parameter(
            name="quantity",
            type="integer",
            description="The quantity of that item to update/modify in the customer's shopping cart",
        ),
    ],
    required_parameters=["name", "quantity"],
)
