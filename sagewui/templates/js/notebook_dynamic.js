///////////////////////////////////////////////////////////////////
//
// "External" Javascript
//
///////////////////////////////////////////////////////////////////


// Key codes (auto-generated in js.py from config.py and user's sage
// config).
 {{ KEY_CODES }}
 
// Other libraries.
{% include "js/async_lib.js" %}

function interrupt_callback(status, response) {
    /*
    Callback called after we send the interrupt signal to the server.
    If the interrupt succeeds, we change the CSS/DOM to indicate that
    no cells are currently computing.  If it fails, we display/update
    a alert and repeat after a timeout.  If the signal doesn't make
    it, we just reset any alerts.
    */
    var is = interrupt_state, message;
    {% set timeout = 5 %}
    var timeout = {{ timeout }};

    if (response === 'failed') {
        if (!is.count) {
            is.count = 1;
            message = Sagewui.translations['Unable to interrupt calculation.'] + " " + Sagewui.translations['Trying again in %(num)d second...'](timeout) + ' ' + Sagewui.translations['Close this box to stop trying.'];

            is.alert = $.achtung({
                className: 'interrupt-fail-notification',
                message: message,
                timeout: timeout,
                hideEffects: false,
                showEffects: false,
                onCloseButton: function () {
                    reset_interrupts();
                },
                onTimeout: function () {
                    interrupt();
                }
            });
            return;
        }

        is.count += 1;
        message = Sagewui.translations['Interrupt attempt'] + " " + is.count;
        if (is.count > 5) {
            message += ". " + Sagewui.translations["<a href='javascript:restart_sage();'>Restart</a>, instead?"];
        }
        is.alert.achtung('update', {
            message: message,
            timeout: timeout
        });
    } else if (status === 'success') {
        halt_queued_cells();
    } else {
        reset_interrupts();
    }
}
