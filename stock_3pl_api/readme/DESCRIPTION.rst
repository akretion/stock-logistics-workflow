Introduction
~~~~~~~~~~~~

Third-party logistics (abbreviated as 3PL, or TPL) in logistics and supply chain management
is an organization's use of third-party businesses to outsource elements of its distribution,
warehousing, and fulfillment services. (Wikipedia)

This module exposes the convenient Odoo stock operations to a 3PL partner with a
**REST API**.
It means the 3PL partner should implement a **REST API client** in order to get Odoo
reflect the stock operations he does physically.
The OCA/wms/shopfloor module has been a source of inspiration. However this
module is simpler as it focuses on higher level operations compared to Shopfloor.

The service uses an **API key** in the HTTP header to authenticate the API user.
An API key is created in the Demo data (for development), using the Demo user.
This demo key to use in the HTTP header API-KEY is: 42D144F7BE780EBD

The API key is associated to an Odoo user and its permissions. You may take
advantage of this in the case of a multi-company set up.

The API exposes 1 main endpoint for consulting the catalog and the inventory:

* GET /stock-3pl-api/product

and 4 main endpoints for consulting the pickings and processing them:

* GET /stock-3pl-api/picking
* GET /stock-3pl-api/picking/<id>
* POST /stock-3pl-api/picking/<id>/done
* POST /stock-3pl-api/picking/<id>

The usage of these endpoints is explained in the following sections.
