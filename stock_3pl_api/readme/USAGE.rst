Catalog and Inventory
~~~~~~~~~~~~~~~~~~~~~

First the 3PL partner can import the catalog and inventory from Odoo with the

Product list endpoint::
  GET /stock-3pl-api/product

Curl example::
  curl -H "API-KEY: 42D144F7BE780EBD"  http://localhost:8069/stock-3pl-api/product

The 3PL partner can typically use this to ensure that the Odoo stock levels
are consistent with its own inventory and warn you otherwise.

TODO what about an API point to warn Odoo about a stock level error?

You can also consult a specific product with its id::
  GET /stock-3pl-api/product/<id>

Curl example::
  curl -H "API-KEY: 42D144F7BE780EBD"  http://localhost:8069/stock-3pl-api/product/10

You can also specify a specific stock_location_name to get the stock levels at
a specific location in case you have a more sophisticated multi-locations usage.
TODO document.


Purchase Orders / Incoming Pickings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module is mostly used to manage your product expeditions. But the 3PL partner
might also inform Odoo about the received products.
Reception works a bit the same as expedition but in fact it is simpler, so let's start talking
about the product reception API (or purchase orders).

The validation of an Odoo purchase orders in Odoo will create an incoming stock.picking
that we can import with the 3PL API:


Getting the list of receptions
==============================

picking list endpoint::
  GET /picking

Curl example::
  curl -v -H "API-KEY: 42D144F7BE780EBD" "http://localhost:8069/stock-3pl-api/picking?picking_type_name=Receipts&states=confirmed|assigned"


stock.picking filters
=====================

You can filter these incoming pickings using the following parameters:

* picking_type_name: use 'Receipts' for reception but in fact you could manage any Odoo picking operation
* states: a string with the value of the Odoo state picking field, or a list of values separated with |
* date_from
* date_to
* id_3pl: use false to filter only the stock pickings with no id_3pl yet. Eventually you will later write an id_3pl in some pickings to help you filter

You can also consult a specific picking with::
  GET /stock-3pl-api/picking/<id>


Processing a stock.picking
==========================

When the products are received, you can simply set the picking to the 'done'
state with all the planed quantities with the:

set to done picking endpoint::
  POST /stock-3pl-api/picking/<id>/done?force_reserved_quantities=true

If you don't specify force_reserved_quantities=true, only the reserved quantities
will be processed, see later how you can inform these reserved quantities with
the API.

Curl example::
  curl -X POST -H "API-KEY: 42D144F7BE780EBD" http://localhost:8069/stock-3pl-api/picking/9/done?force_reserved_quantities=true

You can ensure in the response that the picking state is 'done'.


But instead you might likely want to inform the processed quantities and eventually
leave a back order to process later.
For this you should first consult the id of the planed stock.move of the picking
in order to inform the done quantity for each move. The field with the list of
planed moves is called 'move_ids_without_package'.

You can consult these move ids either from the picking list either with:

The picking detail endpoint::
  GET /stock-3pl-api/picking/<id>

So suppose you you have a single move an id 36 and with a planed move quantity of 35.
If you want to inform you processed only 30 products, you can use:

set to done picking endpoint with detailed quantities::
  POST /stock-3pl-api/picking/<id>/done --data '{"moves":[{"id":<move_id>, "quantity_done": <move_qty>}, ...]}'

Curl example::
  curl -X POST -v -H "API-KEY: 42D144F7BE780EBD"  --header "Content-Type: application/json" --data '{"moves":[{"id":36, "quantity_done": 30}]}' "http://localhost:8069/stock-3pl-api/picking/26/done"

See the API specification detail in Swagger or Postman for all the options.

With such a command you will leave a backorder open for later reception,
after setting the picking to done, you will get the list of open backorder ids
in the **backorder_ids** response parameter.

If instead you don't want to leave any open backorder, you can pass the
cancel_backorder=true parameter. In this case you may still have a backorder
after processing a picking, but its state will be "cancel" so it won't be
active.

Updating reserved quantity or other picking information without actually
processing the picking can be achieved using the update endpoint that
accepts similar parameters as the the done endpoint.

update endpoint::
  POST /stock-3pl-api/picking/<id>/update

Curl example::
  curl -X POST -v -H "API-KEY: 42D144F7BE780EBD"  --header "Content-Type: application/json" --data '{"moves":[{"id":31, "quantity_done": 30}]}' "http://localhost:8069/stock-3pl-api/picking/21/update"

See the API specification detail for all the options.
You can then use the "/POST done" endpoint to process the picking in this case
you don't need to repeat the moves details when setting the picking to done.


Sale Orders / Outgoing Pickings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Managing the product expeditions is very similar to managing the product reception
as explained in the previous section, except it is more complex because of
the packages and tracking information.

the validation of sale orders in Odoo will create outgoing stock.picking that
we can import in 3PL using the **GET /picking endpoint**.

Curl example::
  curl -v -H "API-KEY: 42D144F7BE780EBD" "http://localhost:8069/stock-3pl-api/picking?picking_type_name=Delivery&states=assigned"

**filters**: you can use the same filters as for the incoming pickings described
in the previous section. Notice that for delivery we use **picking_type_name=Delivery**.
If you filter using states=assigned you will get only deliveries with enough stock
to be processed. Instead you can use states=confirmed|assigned if you want also
the confirmed pickings with not enough stock.

Another filter you may want to use is **id_3pl=false** to get only the new
deliveries for which you have not assigned any id_3pl yet.

You can simply process the delivery pickings with the **/done and /update endpoints**
just like for incoming pickings.


Packaging and tracking information
==================================

But one important thing you can do is set packages and tracking information
if you need.

To do this you should not simply pass the quantity done for each picking move,
but you should instead detail for each move, the list of packages,
with the package ref, quantity, weight and tracking_url eventually.

For instance::
curl -X POST -H "API_KEY: 42D144F7BE780EBD" --header "Content-Type: application/json" \
--data '{"moves":[{"id":11, "lines":[{"quantity": 5, "package": {"ref": "box1"}}, {"quantity": 10, "package": {"ref": "box2"}}]}]}' \
"http://localhost:8069/stock-3pl-api/picking/1/done"

TODO picture links


And also you can use /update endpoint instead to update the picking detail without
actually processing it yet. And you can process it later using /done.
See the API specification for the details.

backorders are handled the same way as for incoming pickings.
