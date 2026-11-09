#include <QtWidgets/QApplication>
#include <QtWidgets/QStyle>
#include <QtWidgets/QStyleOption>
#include <QtGui/QFontMetrics>
#include <QtGui/QIcon>
#include <QtGui/QPaintDevice>
#include <QtGui/QPixmap>
#include <cstdio>

class InvalidDpiDevice : public QPaintDevice {
public:
    QPaintEngine *paintEngine() const override { return nullptr; }
protected:
    int metric(PaintDeviceMetric metric) const override
    {
        if (metric == PdmDpiX || metric == PdmDpiY)
            return 0;
        return QPaintDevice::metric(metric);
    }
};

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (!QCoreApplication::testAttribute(Qt::AA_Use96Dpi)) {
        fprintf(stderr, "DPI preload did not set AA_Use96Dpi\n");
        return 1;
    }
    QApplication::setStyle("Fusion");

    InvalidDpiDevice device;
    QStyleOption option;
    option.fontMetrics = QFontMetrics(app.font(), &device);

    // Demonstrate the broken metric path, then verify the preload's attribute
    // overrides invalid font DPI for both icons and tree indentation.
    QCoreApplication::setAttribute(Qt::AA_Use96Dpi, false);
    const int broken = app.style()->pixelMetric(QStyle::PM_SmallIconSize, &option);
    QCoreApplication::setAttribute(Qt::AA_Use96Dpi);
    const int size = app.style()->pixelMetric(QStyle::PM_SmallIconSize, &option);
    const int indent = app.style()->pixelMetric(QStyle::PM_TreeViewIndentation, &option);
    fprintf(stderr, "fontDpi=%.3f brokenIconSize=%d fixedIconSize=%d treeIndent=%d\n",
            static_cast<double>(option.fontMetrics.fontDpi()), broken, size, indent);
    if (broken > 0 || size != 16 || indent <= 0)
        return 2;

    QPixmap source(16, 16);
    source.fill(Qt::red);
    const auto selected = QIcon(source).pixmap(QSize(size, size), QIcon::Selected);
    if (selected.isNull() || selected.size() != QSize(size, size))
        return 3;
    return 0;
}
