import pandas as pd
import numpy as np
from skimage import measure
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import widgets


Path = mpath.Path
# Load the image
image = plt.imread('mall_plan1.png')

# Convert the image to grayscale
gray_image = np.mean(image, axis=2)

# Find the contours of the object
contours = measure.find_contours(gray_image, level=0.5)

# Plot the image and the contours
fig, ax = plt.subplots()

contours_pd = pd.DataFrame(data=contours, columns=['vertices'])

codes = []
for i in range(len(contours_pd['vertices'])):
    code = [Path.LINETO for k in range(len(contours_pd['vertices'][i]))]
    code[0] = Path.MOVETO
    codes.append(code)
contours_pd['codes'] = codes

numeration = [i for i in range(len(contours_pd['codes']))]
contours_pd['number'] = numeration


def extract_coordinates(arrays):
    x_coords = [coord[0] for coord in arrays]
    y_coords = [coord[1] for coord in arrays]
    return pd.Series({'x': x_coords, 'y': y_coords})


contours_pd[['x', 'y']] = contours_pd['vertices'].apply(extract_coordinates)


def get_center(x_coord, y_coord):
    x_center = x_coord.apply(sum).astype(int) / x_coord.apply(len).astype(int)
    y_center = y_coord.apply(sum).astype(int) / y_coord.apply(len).astype(int)
    return [x_center, y_center]


contours_pd['center_x'] = contours_pd['x'].apply(sum).astype(int) / contours_pd['x'].apply(len).astype(int)
contours_pd['center_y'] = contours_pd['y'].apply(sum).astype(int) / contours_pd['y'].apply(len).astype(int)
duplicates = (contours_pd['number'] == 73) | \
             (contours_pd['number'] == 72) | \
             (contours_pd['number'] == 39) | \
             (contours_pd['number'] == 59) | \
             (contours_pd['number'] == 28) | \
             (contours_pd['number'] == 37) | \
             (contours_pd['number'] == 8) | \
             (contours_pd['number'] == 10) | \
             (contours_pd['number'] == 2) | \
             (contours_pd['number'] == 3) | \
             (contours_pd['number'] == 5) | \
             (contours_pd['number'] == 71) | \
             (contours_pd['number'] == 54) | \
             (contours_pd['number'] == 7) | \
             (contours_pd['number'] == 14) | \
             (contours_pd['number'] == 4) | (contours_pd['number'] == 41) | (contours_pd['number'] == 0) | (contours_pd['number'] == 70)
contours_pd = contours_pd.drop(contours_pd[duplicates].index)
contours_pd = contours_pd.reset_index(drop=True)
stores = pd.read_excel('stores.xlsx')
contours_pd['names'] = stores['Stores']
contours_pd['turnover'] = stores['Turnover']
contours_pd['rent_m2'] = stores['Rent_per_m2']
contours_pd['OCR'] = stores['OCR']

# define a colormap
cmap = plt.cm.get_cmap('Blues')

patches = []


def build_contours(i):
    color = cmap(contours_pd['turnover'][i])
    path = mpath.Path(contours_pd['vertices'][i], contours_pd['codes'][i])
    patch = mpatches.PathPatch(path, facecolor=color, alpha=0.5)
    ax.add_patch(patch)
    annot = ax.annotate("", xy=(contours_pd['center_x'][i], contours_pd['center_y'][i]),
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"), textcoords="offset points", xytext=(20, 20))
    patches.append(patch)
    ax.axis('image')
    ax.set_xticks([])
    ax.set_yticks([])

    def update_annot(ind):
        annot.xy = (contours_pd['center_x'][i], contours_pd['center_y'][i])
        text = f"{contours_pd['names'][i]}\nTurnover - {contours_pd['turnover'][i]} mln. USD"
        annot.set_text(text)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = patch.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)


for i in range(len(contours_pd['codes'])):
    build_contours(i)

#slider widget
slider_ax = plt.axes([0.2, 0.05, 0.6, 0.03])
slider = widgets.RangeSlider(slider_ax, 'Turnover',
                             min(contours_pd['turnover']),
                             max(contours_pd['turnover']),
                             valinit=(min(contours_pd['turnover']), max(contours_pd['turnover'])))


def update(val):
    min_val, max_val = slider.val
    filtered_pd = contours_pd[(contours_pd['turnover'] >= min_val) & (contours_pd['turnover'] <= max_val)]
    for i in range(len(contours_pd['codes'])):
        if i in filtered_pd.index:
            patches[i].set_visible(True)
        else:
            patches[i].set_visible(False)
    plt.draw()


slider.on_changed(update)

# create a dictionary mapping store names to their indices in the contours_pd DataFrame
store_patches = {name: patch for name, patch in zip(contours_pd['names'], patches)}


def on_text_change(label):
    if not label:
        # If the label is empty, show all patches
        for patch in store_patches.values():
            patch.set_alpha(0.5)
        # If the label is empty, show all patches and hide all annotations and images
        for annot in ax.texts:
            annot.set_visible(False)
    else:
        # Otherwise, hide all patches except the selected store and show its annotation and image
        for name, patch in store_patches.items():
            if name == label:
                patch.set_alpha(0.5)
                annot = ax.annotate(f"{name}\nOCR - {float(contours_pd['OCR'].loc[contours_pd['names']==name])}",
                                    xy=(1.1, 0.5),
                                    xycoords='axes fraction',
                                    fontsize=12, ha='left')
                annot.set_visible(True)
            else:
                patch.set_alpha(0.1)
        for annot in ax.texts:
            if label in annot.get_text():
                annot.set_visible(True)
            else:
                annot.set_visible(False)

    fig.canvas.draw_idle()


# create Textbox widget
textbox = widgets.TextBox(plt.axes([0.2, 0.9, 0.6, 0.05]), '')
textbox.on_text_change(on_text_change)


sm = plt.cm.ScalarMappable(cmap=cmap)
sm.set_array(contours_pd['number'])
plt.colorbar(sm)
plt.show()
