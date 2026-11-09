#include <QtCore/QCoreApplication>

namespace {
void use96Dpi()
{
    // XWayland can temporarily expose a 0x0 virtual screen during display
    // power-off. Qt5 then propagates NaN logical DPI into fonts/style metrics.
    // Unlike QT_FONT_DPI, AA_Use96Dpi is explicitly checked by QStyleHelper::dpi
    // before consulting QStyleOption's potentially corrupted font metrics.
    QCoreApplication::setAttribute(Qt::AA_Use96Dpi);
}
Q_COREAPP_STARTUP_FUNCTION(use96Dpi)
} // namespace
