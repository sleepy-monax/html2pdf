from dataclasses import dataclass
from typing import Optional


@dataclass
class Margins:
    top: float
    bottom: float
    left: float
    right: float

    def __init__(
            self,
            top: Optional[float] = None,
            bottom: Optional[float] = None,
            left: Optional[float] = None,
            right: Optional[float] = None,
            all: Optional[float] = None,
            horiz: Optional[float] = None,
            vert: Optional[float] = None):

        if all is not None:
            self.top = all
            self.bottom = all
            self.left = all
            self.right = all

        if horiz is not None:
            self.left = horiz
            self.right = horiz

        if vert is not None:
            self.top = vert
            self.bottom = vert

        self.top = top or self.top or 0.0
        self.bottom = bottom or self.bottom or 0.0
        self.left = left or self.left or 0.0
        self.right = right or self.right or 0.0

@dataclass
class Stock:
    key: str
    description: str
    height: float
    width: float


def A(n):
    h = 1189.0/(2**(n-1))
    w = 841.0/(2**(n-1))

    return Stock(
        key=f'a{n}',
        description=f'A{n}  {n+4}   {h} x {w} mm',
        height=h,
        width=w,
    )


def B(n):
    h = 1000.0/(2**(n-1))
    w = 707.0/(2**(n-1))

    return Stock(
        key=f'b{n}',
        description=f'B{n}  {n+4}   {h} x {w} mm',
        height=h,
        width=w,
    )


C5E = Stock(
    key='c5e',
    description='C5E 24  163 x 229 mm',
    height=229.0,
    width=163.0,
)

COMM10E = Stock(
    key='comm10e',
    description='Comm10E 25  105 x 241 mm, U.S. Common 10 Envelope',
    height=241.0,
    width=105.0,
)

DLE = Stock(
    key='dle',
    description='DLE 26 110 x 220 mm',
    height=220.0,
    width=110.0,
)

EXECUTIVE = Stock(
    key='executive',
    description='Executive 4   7.5 x 10 inches, 190.5 x 254 mm',
    height=254.0,
    width=190.5,
)

FOLIO = Stock(
    key='folio',
    description='Folio 27  210 x 330 mm',
    height=330.0,
    width=210.0,
)

LEDGER = Stock(
    key='ledger',
    description='Ledger  28  431.8 x 279.4 mm',
    height=279.4,
    width=431.8,
)

LEGAL = Stock(
    key='legal',
    description='Legal    3   8.5 x 14 inches, 215.9 x 355.6 mm',
    height=355.6,
    width=215.9,
)

LETTER = Stock(
    key='letter',
    description='Letter 2 8.5 x 11 inches, 215.9 x 279.4 mm',
    height=279.4,
    width=215.9,
)

TABLOID = Stock(
    key='tabloid',
    description='Tabloid 29 279.4 x 431.8 mm',
    height=431.8,
    width=279.4,
)

STOCKS = [
    A(0), A(1), A(2), A(3), A(4), A(5), A(6), A(7), A(8), A(9), A(10),
    B(0), B(1), B(2), B(3), B(4), B(5), B(6), B(7), B(8), B(9), B(10),
    C5E, COMM10E, DLE, EXECUTIVE, FOLIO, LEDGER, LEGAL, LETTER, TABLOID,
]

NAMES = [s.key for s in STOCKS]
