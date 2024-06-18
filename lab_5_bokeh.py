from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh.models import Slider, CheckboxGroup, Button
import numpy as np
from scipy.signal import butter, filtfilt
import sys
import subprocess

def harmonic(t, amplitude, frequency, phase):
    return amplitude * np.sin(2 * np.pi * frequency * t + phase)

def create_noise(t, noise_mean, noise_covariance):
    return np.random.normal(noise_mean, np.sqrt(noise_covariance), len(t))

def harmonic_with_noise(t, amplitude, frequency, phase=0, noise_mean=0, noise_covariance=0.1, noise=None):
    harmonic_signal = harmonic(t, amplitude, frequency, phase)
    if noise is not None:
        return harmonic_signal + noise
    else:
        global noise_g
        noise_g = create_noise(t, noise_mean, noise_covariance)
        return harmonic_signal + noise_g

def moving_avg(data, window_size):
    moving_avg = []
    window_size = int(window_size)
    for i in range(len(data)):
        temp_winsize = min(window_size, i, len(data) - i)
        avg = np.mean(data[i - window_size//2 : i + (window_size)//2])
        moving_avg.append(avg)
    return moving_avg

initial_amplitude = 1.0
initial_frequency = 1.0
initial_phase = 0.0
initial_noise_mean = 0.0
initial_noise_covariance = 0.1
noise_g = None

t = np.linspace(0, 10, 1000)
sampling_frequency = 1 / (t[1] - t[0])

plot = figure(title="Гармонійний сигнал з шумом та низькочастотним фільтром", x_axis_label='Час', y_axis_label='Амплітуда',
              width=1200, height=600, sizing_mode="scale_width", background_fill_color='#fff0f5')

harmonic_line = plot.line(t, harmonic(t, initial_amplitude, initial_frequency, initial_phase), line_width=3,
                          color='#ff69b4', line_dash='dashed', legend_label='Гармонійний сигнал')

with_noise_line = plot.line(t, harmonic_with_noise(t, initial_amplitude, frequency=initial_frequency,
                                                   phase=initial_phase, noise_mean=initial_noise_mean,
                                                   noise_covariance=initial_noise_covariance, noise=None),
                            line_width=3, color='#ff1493', legend_label='Сигнал з шумом')

filtered_signal = moving_avg(with_noise_line.data_source.data['y'], sampling_frequency)
l_filtered = plot.line(t, filtered_signal, line_width=3, color='#db7093', legend_label='Фільтрований сигнал')

s_amplitude = Slider(title="Амплітуда", value=initial_amplitude, start=0.1, end=10.0, step=0.1, bar_color='#ff69b4')
s_frequency = Slider(title="Частота", value=initial_frequency, start=0.1, end=10.0, step=0.1, bar_color='#ff69b4')
s_phase = Slider(title="Фаза", value=initial_phase, start=0.0, end=2 * np.pi, step=0.1, bar_color='#ff69b4')
s_noise_mean = Slider(title="Середнє шуму", value=initial_noise_mean, start=-1.0, end=1.0, step=0.1, bar_color='#ff1493')
s_noise_covariance = Slider(title="Дисперсія шуму", value=initial_noise_covariance, start=0.0, end=1.0, step=0.1, bar_color='#ff1493')
s_cutoff_frequency = Slider(title="Розмір вікна", value=3, start=1, end=35.0, step=1, bar_color='#db7093')

cb_show_noise = CheckboxGroup(labels=['Показати шум'], active=[0], width=200)
button_regenerate_noise = Button(label='Перегенерувати шум', button_type="success", width=200)
button_random_params = Button(label='Випадкові параметри', button_type="warning", width=200)
button_reset = Button(label='Скинути', button_type="danger", width=200)

def update(attrname, old, new):
    amplitude = s_amplitude.value
    frequency = s_frequency.value
    phase = s_phase.value

    noise_mean = s_noise_mean.value
    noise_covariance = s_noise_covariance.value

    global initial_noise_mean, initial_noise_covariance, noise_g

    if initial_noise_covariance != noise_covariance or initial_noise_mean != noise_mean:
        initial_noise_mean = noise_mean
        initial_noise_covariance = noise_covariance
        noise_g = create_noise(t, noise_mean, noise_covariance)

    show_noise = bool(new)
    harmonic_line.data_source.data['y'] = harmonic(t, amplitude, frequency, phase)
    with_noise_line.data_source.data['y'] = harmonic_with_noise(t, amplitude, frequency, phase,
                                                                noise_mean, noise_covariance, noise_g)
    with_noise_line.visible = show_noise

    cutoff_frequency = s_cutoff_frequency.value
    filtered_signal = moving_avg(with_noise_line.data_source.data['y'], cutoff_frequency)
    l_filtered.data_source.data['y'] = filtered_signal

def regenerate_noise():
    with_noise_line.data_source.data['y'] = harmonic_with_noise(t, s_amplitude.value, s_frequency.value, s_phase.value,
                                                                s_noise_mean.value, s_noise_covariance.value)

def random_params():
    s_amplitude.value = np.random.uniform(0.1, 10.0)
    s_frequency.value = np.random.uniform(0.1, 10.0)
    s_phase.value = np.random.uniform(0.0, 2 * np.pi)
    s_noise_mean.value = np.random.uniform(-1.0, 1.0)
    s_noise_covariance.value = np.random.uniform(0.0, 1.0)
    regenerate_noise()

def reset_params():
    s_amplitude.value = initial_amplitude
    s_frequency.value = initial_frequency
    s_phase.value = initial_phase
    s_noise_mean.value = 0.0
    s_noise_covariance.value = 0.1
    s_cutoff_frequency.value = 3
    cb_show_noise.active = [0]
    regenerate_noise()

s_amplitude.on_change('value', update)
s_frequency.on_change('value', update)
s_phase.on_change('value', update)
s_noise_mean.on_change('value', update)
s_noise_covariance.on_change('value', update)
s_cutoff_frequency.on_change('value', update)
cb_show_noise.on_change('active', update)
button_regenerate_noise.on_click(regenerate_noise)
button_random_params.on_click(random_params)
button_reset.on_click(reset_params)

layout = column(plot,
                column(row(s_amplitude, s_frequency, s_phase),
                       row(s_noise_mean, s_noise_covariance, s_cutoff_frequency),
                       row(cb_show_noise, button_regenerate_noise, button_random_params, button_reset),
                       sizing_mode='stretch_width', align='center'))

curdoc().add_root(layout)

if __name__ == "__main__":
    with open("lab_5_bokeh.py", "w", encoding="utf-8") as f:
        f.write(__import__("inspect").getsource(sys.modules[__name__]))
    subprocess.run(["bokeh", "serve", "--show", "lab_5_bokeh.py"])
