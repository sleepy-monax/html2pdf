#pragma once

#include <karm-base/rc.h>
#include <webkit2/webkit2.h>

namespace Odoo::Html2pdf {

struct Printer : public Meta::Static {
    WebKitWebView *_webView;

    static void _onLoadChanged(
        WebKitWebView *webView,
        WebKitLoadEvent loadEvent,
        Printer *self) {
    }

    Printer(WebKitWebView *webView)
        : _webView(webView) {
        g_signal_connect(_webView, "load-changed", G_CALLBACK(_onLoadChanged), this);
    }

    static Strong<Printer> create() {
        auto *webView = WEBKIT_WEB_VIEW(webkit_web_view_new());
        return makeStrong<Printer>(webView);
    }

    Res<Buf<Byte>> print() {
        auto *printOperation = webkit_print_operation_new(_webView);
        webkit_print_operation_run_dialog(printOperation, nullptr);
        return Ok();
    }
};

} // namespace Odoo::Html2pdf
