1.  Go to **Inventory** dashboard and open any picking.
2.  If picking state is **available** you can see an split button.
3.  Click on **Split** and choose a mode:
    - *Reserved quantities*: on the "Operations" tab, fill the field "Done"
      to the quantity you want to split for each line. The wizard splits the
      current picking into two different pickings depending on the quantities
      done you entered above.
    - *Manual quantities*: on the "Operations" tab, fill the column
      "Quantity to Split" for each line you want to split off. The entered
      quantity is extracted in a new picking, the rest of the demand stays in
      the original picking. The "Done" quantities are not modified.
    - *One picking per move*: the first move is extracted in a new picking.
    - *Select move lines to split off*: the selected moves are extracted in a
      new picking.
4.  Both pickings remain confirmed.
5.  When splitting a picking in an unassigned state, wizard won't be
    auto completed with picking lines.
