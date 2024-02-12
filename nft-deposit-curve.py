import matplotlib.pyplot as plt
import numpy as np

from matplotlib.widgets import Button, Slider


# The parametrized function to be plotted
def f(x, a, b):
    return 0.2 / (1 + np.exp(a - b * x))

t = np.linspace(0, 1000000, 100000)

# Define initial parameters
init_a = 0.1
init_b = 0.00001

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
line, = ax.plot(t, f(t, init_a, init_b), lw=2)
ax.set_xlabel('Collections')
ax.set_ylabel('Deposit [DOT]')

# adjust the main plot to make room for the sliders
fig.subplots_adjust(left=0.25, bottom=0.25)

# Make a horizontal slider to control the b.
axb = fig.add_axes([0.25, 0.1, 0.65, 0.03])
b_slider = Slider(
    ax=axb,
    label='b',
    valmin=0.0000001,
    valmax=0.00002,
    valinit=init_b,
)

# Make a vertically oriented slider to control the a
axa = fig.add_axes([0.1, 0.25, 0.0225, 0.63])
a_slider = Slider(
    ax=axa,
    label="a",
    valmin=0.0,
    valmax=1,
    valinit=init_a,
    orientation="vertical"
)


# The function to be called anytime a slider's value changes
def update(val):
    line.set_ydata(f(t, a_slider.val, b_slider.val))
    fig.canvas.draw_idle()


# register the update function with each slider
b_slider.on_changed(update)
a_slider.on_changed(update)

# Create a `matplotlib.widgets.Button` to reset the sliders to initial values.
resetax = fig.add_axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', hovercolor='0.975')

def reset(event):
    b_slider.reset()
    a_slider.reset()
button.on_clicked(reset)

plt.show()
