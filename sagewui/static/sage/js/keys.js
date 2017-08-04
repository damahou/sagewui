/*
Notebook Keybindings

This module is responsible for setting the keyboard bindings for the notebook.

These are the standard key and mouse bindings available in the
notebook:

- *Evaluate Input:* Press **shift-enter**. You can start several calculations
  at once. If you press **alt-enter** instead, then a new cell is created after
  the current one. If you press **ctrl-enter** then the cell is split and both
  pieces are evaluated separately.

..

- *Tab Completion:* Press **tab** while the cursor is on an identifier. On some
  web browsers (e.g., Opera) you must use control-space instead of tab.

..

- *Insert New Cell:* Put the mouse between an output and input until the
  horizontal line appears and click. If you press Alt-Enter in a cell, the cell
  is evaluated and a new cell is inserted after it.

..

- *Delete Cell:* Delete all cell contents, then press **backspace**.

..

- *Split and Join Cells:* Press **ctrl-;** in a cell to split it into two
  cells, and **ctrl-backspace** to join them. Press **ctrl-enter** to split a
  cell and evaluate both pieces.

..

- *Insert New HTML Cell:* Shift click between cells to create a new HTML cell.
  Double click on existing HTML to edit it. Use \$...\$ and \$\$...\$\$ to
  include typeset math in the HTML block.

..

- *Hide/Show Output:* Click on the left side of output to toggle between
  hidden, shown with word wrap, and shown without word wrap.

..

- *Indenting Blocks:* Highlight text and press **>** to indent it all and **<**
  to unindent it all (works in Safari and Firefox). In Firefox you can also
  press tab and shift-tab.

..

- *Comment/Uncomment Blocks:* Highlight text and press **ctrl-.** to comment it
  and **ctrl-,** to uncomment it. Alternatively, use **ctrl-3** and **ctrl-4**.

..

- *Parenthesis matching:* To fix unmatched or mis-matched parentheses, braces
  or brackets, press **ctrl-0**.  Parentheses, brackets or braces to the left
  of or above the cursor will be matched, minding strings and comments.  Note,
  only Python comments are recognized, so this won\'t work for c-style
  multiline comments, etc.

*/


(function(app) {
    var mod_ALT = 1
    var mod_CTRL = 2
    var mod_SHIFT = 4

    app.keys = {
        request_introspections(e) {
            return ((e.m==KEY_SPC)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_TAB)&&(e.v==(0)));
        },
        indent(e) {
            return ((e.m==KEY_TAB)&&(e.v==(0)))||
                   ((e.m==KEY_GT)&&(e.v==(0)));
        },
        unindent(e) {
            return ((e.m==KEY_TAB)&&(e.v==(0 | mod_SHIFT)))||
                   ((e.m==KEY_LT)&&(e.v==(0)));
        },
        request_history(e) {
            return ((e.m==KEY_Q)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_QQ)&&(e.v==(0 | mod_CTRL)));
        },
        request_log(e) {
            return ((e.m==KEY_P)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_PP)&&(e.v==(0 | mod_CTRL)));
        },
        close_helper(e) {
            return ((e.m==KEY_ESC)&&(e.v==(0)));
        },
        interrupt(e) {
            return ((e.m==KEY_ESC)&&(e.v==(0)));
        },
        send_input(e) {
            return ((e.m==KEY_RETURN)&&(e.v==(0 | mod_SHIFT)))||
                   ((e.m==KEY_ENTER)&&(e.v==(0 | mod_SHIFT)));
        },
        send_input_newcell(e) {
            return ((e.m==KEY_RETURN)&&(e.v==(0 | mod_ALT)))||
                   ((e.m==KEY_ENTER)&&(e.v==(0 | mod_ALT)));
        },
        // missing
        prev_cell(e) {
            return ((e.m==KEY_UP)&&(e.v==(0 | mod_CTRL)));
        },
        // missing
        next_cell(e) {
            return ((e.m==KEY_DOWN)&&(e.v==(0 | mod_CTRL)));
        },
        page_up(e) {
            return ((e.m==KEY_PGUP)&&(e.v==(0)));
        },
        page_down(e) {
            return ((e.m==KEY_PGDN)&&(e.v==(0)));
        },
        delete_cell(e) {
            return ((e.m==KEY_BKSPC)&&(e.v==(0)));
        },
        // missing
        generic_submit(e) {
            return ((e.m==KEY_ENTER)&&(e.v==(0)));
        },
        up_arrow(e) {
            return ((e.m==KEY_UP)&&(e.v==(0)));
        },
        down_arrow(e) {
            return ((e.m==KEY_DOWN)&&(e.v==(0)));
        },
        comment(e) {
            return ((e.m==KEY_DOT)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_3)&&(e.v==(0 | mod_CTRL)));
        },
        uncomment(e) {
            return ((e.m==KEY_COMMA)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_4)&&(e.v==(0 | mod_CTRL)));
        },
        fix_paren(e) {
            return ((e.m==KEY_0)&&(e.v==(0 | mod_CTRL)));
        },

        control(e) {
            return ((e.m==KEY_CTRL)&&(e.v==(0)));
        },
        // missing
        backspace(e) {
            return ((e.m==KEY_BKSPC)&&(e.v==(0)));
        },
        enter(e) {
            return ((e.m==KEY_ENTER)&&(e.v==(0)))||
                   ((e.m==KEY_RETURN)&&(e.v==(0)));
        },
        // missing
        enter_shift(e) {
            return ((e.m==KEY_ENTER)&&(e.v==(0 | mod_SHIFT)))||
                   ((e.m==KEY_RETURN)&&(e.v==(0 | mod_SHIFT)));
        },
        spliteval_cell(e) {
            return ((e.m==KEY_ENTER)&&(e.v==(0 | mod_CTRL)))||
                   ((e.m==KEY_RETURN)&&(e.v==(0 | mod_CTRL)))||
                           // needed on OS X Firefox
                   ((e.m==KEY_CTRLENTER)&&(e.v==(0 | mod_CTRL)));
        },
        join_cell(e) {
            return ((e.m==KEY_BKSPC)&&(e.v==(0 | mod_CTRL)));
        },
        split_cell(e) {
            return ((e.m==KEY_SEMI)&&(e.v==(0 | mod_CTRL)));
        },
        split_cell_noctrl(e) {
            return ((e.m==KEY_SEMI)&&(e.v==(0)));
        },

        menu_left(e) {
            return ((e.m==KEY_LEFT)&&(e.v==(0)));
        },
        menu_up(e) {
            return ((e.m==KEY_UP)&&(e.v==(0)));
        },
        menu_right(e) {
            return ((e.m==KEY_RIGHT)&&(e.v==(0)));
        },
        menu_down(e) {
            return ((e.m==KEY_DOWN)&&(e.v==(0)));
        },
        menu_pick(e) {
            return ((e.m==KEY_ENTER)&&(e.v==(0)))||
                   ((e.m==KEY_RETURN)&&(e.v==(0)));
        },
    };
})(window.Sagewui || (window.Sagewui = {}));
// 8  -- backspace
// 9  -- tab
// 13 -- return
// 27 -- esc
// 32 -- space
// 37 -- left
// 38 -- up
// 39 -- right
// 40 -- down
