import matplotlib.pyplot as plt
import numpy as np

from matplotlib.widgets import Button, Slider

# The parametrized function to be plotted
def f(x, k, x0):
    # Adjusted to reflect the new function with MIN_DOT and MAX_DOT
    MIN_DOT = 0.005
    MAX_DOT = 0.2
    return MIN_DOT + (MAX_DOT - MIN_DOT) / (1 + np.exp(k * x0 - k * x ))

# Time points to plot
t = np.linspace(0, 1000000, 100000)

# a in the code is = x0 and b in the code is = k
init_k = 0.00001  # Initial steepness
init_x0 = 500000  # Initial midpoint of the sigmoid

fig, ax = plt.subplots()
line, = ax.plot(t, f(t, init_k, init_x0), lw=2)
ax.set_xlabel('Collections')
ax.set_ylabel('Deposit [DOT]')

fig.subplots_adjust(left=0.25, bottom=0.25)

axk = fig.add_axes([0.25, 0.1, 0.65, 0.03])
k_slider = Slider(
    ax=axk,
    label='Steepness (k)',
    valmin=0.0000001,
    valmax=0.0001,
    valinit=init_k,
)

axx0 = fig.add_axes([0.1, 0.25, 0.0225, 0.63])
x0_slider = Slider(
    ax=axx0,
    label="Midpoint (x0)",
    valmin=0,
    valmax=1000000,
    valinit=init_x0,
    orientation="vertical"
)

def update(val):
    line.set_ydata(f(t, k_slider.val, x0_slider.val))
    fig.canvas.draw_idle()

k_slider.on_changed(update)
x0_slider.on_changed(update)

resetax = fig.add_axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', hovercolor='0.975')

def reset(event):
    k_slider.reset()
    x0_slider.reset()
button.on_clicked(reset)

plt.show()
