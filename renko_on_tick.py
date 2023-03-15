import numpy as np
from numba import njit

@njit
def renko_numba(tick_prices: np.ndarray, brick_size: float) -> np.ndarray:
    
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
    
    return np.array(renko_data)
