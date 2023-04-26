import io

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

w, h = A4
PAGE_HEIGHT = h
PAGE_WIDTH = w


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        FONT_NUM = 9
        LINEWIDTH = 0.1
        STROKE_COLOR_ZERO = 0
        ALPHA_NUM = 0.2
        ALPHA_NUM_FOUR = 0.4
        ONE_FIVE_NUM = 1.5
        STRING_NUM_DRAW = 1.1
        self.setFont('Times-Roman', FONT_NUM)
        self.setLineWidth(LINEWIDTH)
        self.setStrokeColor(Color(
            STROKE_COLOR_ZERO, STROKE_COLOR_ZERO, STROKE_COLOR_ZERO,
            alpha=ALPHA_NUM))
        self.setFillColor(Color(
            STROKE_COLOR_ZERO, STROKE_COLOR_ZERO, STROKE_COLOR_ZERO,
            alpha=ALPHA_NUM_FOUR))
        self.line(cm, ONE_FIVE_NUM * cm, A4[STROKE_COLOR_ZERO] - cm,
                  ONE_FIVE_NUM * cm)
        self.drawRightString(
            A4[STROKE_COLOR_ZERO] - cm,
            STRING_NUM_DRAW * cm,
            "Page %d of %d" % (self._pageNumber, page_count),
        )


def first_page(canvas, doc):
    FONT_NUM = 15
    WIDTH_NUM = 2.0
    HEIGHT_NUM = 38
    canvas.saveState()
    canvas.setFont('DejaVuSerif', FONT_NUM)
    canvas.drawCentredString(PAGE_WIDTH / WIDTH_NUM,
                             PAGE_HEIGHT - HEIGHT_NUM, doc.title)
    doc.afterPage()
    canvas.restoreState()


def later_pages(canvas, doc):
    FONT_NUM = 9
    canvas.saveState()
    canvas.setFont('DejaVuSerif', FONT_NUM)
    canvas.restoreState()


def get_shopping_list_text(
        ingredient__name, ingredient__measurement_unit, amount
):
    return (
        f'{ingredient__name}'
        f' ({ingredient__measurement_unit}) - {amount}'
    )


def create_pdf_from_queryset(queryset, username):
    SIZE_NUM = 0.75
    SPACE_NUM = 2.5
    pdf_file = io.BytesIO()
    ru_style = getSampleStyleSheet()['Normal']
    ru_style.fontName = 'DejaVuSerif'
    doc = SimpleDocTemplate(
        pdf_file,
        leftMargin=SIZE_NUM * inch,
        rightMargin=SIZE_NUM * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )
    pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf', 'UTF-8'))
    doc.title = f'Список покупок для {username}'
    story = [Spacer(SPACE_NUM, SIZE_NUM * inch)]
    for items in queryset:
        story.append(Paragraph(get_shopping_list_text(**items), ru_style))

    story.append(PageBreak())
    doc.build(
        story,
        onFirstPage=my_first_page,
        onLaterPages=my_later_pages,
        canvasmaker=NumberedCanvas,
    )
    pdf_file.seek(0)
    return pdf_file
