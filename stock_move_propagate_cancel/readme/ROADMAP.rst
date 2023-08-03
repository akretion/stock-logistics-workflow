This module aims to manage most of cancelation cases among chained stock moves. But the subject can become really complex as anything is possible in Odoo.
One can change the quantity of a chained move for example resulting in an inconsistent situation when all part of the chain don't have the same quantity.

We can also have scenarios where a stock move have multiple destination moves, each with a different destination location. In this case, if the initial stock move is partially canceled, Odoo can't know on which destination move the propagation should be canceled.

For all these cases the module does nothing to avoid making a mistake.

The module works with the following rules :
In case of a cancelation of a stock move with the cancelation propagation option activated, odoo find the quantity of the siblings move which has not been canceled (either it is done or waiting to be processed).
Then, it wil only propagate the cancelation on the destination moves if those keep a quantity of products done or to do equal or bigger than the previous moves.

So, in these situations, the module don't cancel anything rather than risking to cancel the wrong destinaton moves/quantities.
