This module improve the stock cancel propagation of Odoo stock module.
In base stock module, a cancelation of destination stock move is only made if all previous stock moves are canceled.
This modules aims to propagate the cancelation even if only part of the previous move is canceled.

In case of chained stock moves, if you transfer a stock move and cancel the backorder, the destination stock move will be splitted and partially canceled to match what has really been transfered.
