
#include <gtk/gtk.h>
#include <karm-main/main.h>
#include <webkit2/webkit2.h>

static void destroyWindowCb(GtkWidget *, GtkWidget *) { gtk_main_quit(); }

static gboolean closeWebViewCb(WebKitWebView *, GtkWidget *window) {
    gtk_widget_destroy(window);
    return TRUE;
}

Res<> entryPoint(Ctx &) {
    gtk_init(nullptr, nullptr);

    GtkWidget *main_window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_default_size(GTK_WINDOW(main_window), 800, 600);

    WebKitWebView *webView = WEBKIT_WEB_VIEW(webkit_web_view_new());
    gtk_container_add(GTK_CONTAINER(main_window), GTK_WIDGET(webView));

    g_signal_connect(main_window, "destroy", G_CALLBACK(destroyWindowCb), NULL);

    g_signal_connect(webView, "close", G_CALLBACK(closeWebViewCb), main_window);

    webkit_web_view_load_uri(webView, "http://www.webkitgtk.org/");

    gtk_widget_grab_focus(GTK_WIDGET(webView));

    gtk_widget_show_all(main_window);
    gtk_main();

    return Ok();
}
