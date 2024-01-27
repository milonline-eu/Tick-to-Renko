import numpy as np
from numba import njit
import numba as nb
from numba.experimental import jitclass

@njit
def renko_numba(tick_prices: np.ndarray, brick_size: float) -> list:
    
    renko_data = []
    last_brick_close = tick_prices[0]
    
    for i in range(len(tick_prices)):
        # Calculate the price change from the very 1st brick
        price_change = tick_prices[i] - last_brick_close
        
        # Calculate the number of bricks thus far 
        num_bricks = int(abs(price_change) / brick_size)
        
        for j in range(num_bricks):
            # Determine if it's an up or down brick
            if price_change > 0:
                open_price = last_brick_close
                close_price = open_price + brick_size
            else:
                open_price = last_brick_close
                close_price = open_price - brick_size
            
            renko_data.append((open_price, close_price))
            
            last_brick_close = close_price
    
    return renko_data


@jitclass
class Renko:
    not_initialized: nb.boolean
    half_point: nb.boolean
    brick_size: nb.uint32
    last_brick_close: nb.int64
    last_brick_timestamp: nb.uint64
    up_border: nb.int64
    down_border: nb.int64
    stamps_open: nb.types.ListType(nb.uint64)
    stamps_close: nb.types.ListType(nb.uint64)
    opens: nb.types.ListType(nb.int64)
    closes: nb.types.ListType(nb.int64)
    directions: nb.types.ListType(nb.int8)
    prices: nb.types.ListType(nb.int64)

    def __init__(self, brick_size=10, half_point=False):
        self.brick_size = brick_size
        self.half_point = half_point
        self.not_initialized = True
        self.stamps_open = nb.typed.List.empty_list(nb.uint64(0))
        self.stamps_close =  nb.typed.List.empty_list(nb.uint64(0))
        self.opens =  nb.typed.List.empty_list(nb.int64(0))
        self.closes =  nb.typed.List.empty_list(nb.int64(0))
        self.directions =  nb.typed.List.empty_list(nb.int8(0))
        self.prices =  nb.typed.List.empty_list(nb.int64(0))

    def initialize(self, timestamp, price):
        if self.half_point:
            x = nb.int32(price / self.brick_size)
            self.last_brick_close = nb.int32(x * self.brick_size + self.brick_size / 2)
        else:
            self.last_brick_close = nb.int32(price // self.brick_size * self.brick_size)
        self.up_border = self.last_brick_close + self.brick_size
        self.down_border = self.last_brick_close - self.brick_size
        self.last_brick_timestamp = timestamp
        #print('initialized', self.last_brick_timestamp, self.down_border, self.last_brick_close, self.up_border)

    def add_brick(self, open_timestamp, close_timestamp, open_price, close_price, direction, price):
        self.stamps_open.append(open_timestamp)
        self.stamps_close.append(close_timestamp)
        self.opens.append(open_price)
        self.closes.append(close_price)
        self.directions.append(direction)
        self.prices.append(price)

    def add_tick(self, timestamp:nb.uint64, bid:nb.int64) -> nb.int8:
        if self.not_initialized:
            self.initialize(timestamp, bid)
            self.not_initialized = False
        else:
            if bid >= self.up_border:
                price_change = bid - self.last_brick_close
                num_bricks = nb.uint32(price_change // self.brick_size)
                for i in range(num_bricks):
                    close_price = self.last_brick_close + self.brick_size
                    self.add_brick(self.last_brick_timestamp, timestamp,
                                   self.last_brick_close, close_price, nb.int8(1), bid)
                    self.last_brick_timestamp = timestamp
                    self.last_brick_close = close_price
                self.up_border = self.last_brick_close + self.brick_size
                self.down_border = self.last_brick_close - self.brick_size
                #print('up  ', price_change, num_bricks, self.down_border, self.last_brick_close, self.up_border)
                return 1

            elif bid <= self.down_border:
                price_change = self.last_brick_close - bid
                num_bricks = nb.uint32(price_change // self.brick_size)
                for i in range(num_bricks):
                    close_price = self.last_brick_close - self.brick_size
                    self.add_brick(self.last_brick_timestamp, timestamp,
                                   self.last_brick_close, close_price, nb.int8(-1), bid)
                    self.last_brick_timestamp = timestamp
                    self.last_brick_close = close_price
                self.up_border = self.last_brick_close + self.brick_size
                self.down_border = self.last_brick_close - self.brick_size
                #print('down', price_change, num_bricks, self.down_border, self.last_brick_close, self.up_border)
                return -1
        return 0
