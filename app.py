import json
import math
import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from plotly import graph_objs as go

from stevesie.services import worker_service
from stevesie import Worker

from config import PUBLIC_MAPBOX_TOKEN, HOME_DEPOT_STORES_WORKER_ID, HOME_DEPOT_SEARCH_WORKER_ID

app = dash.Dash()

app.title = 'Home Depot Cheapo - Local Home Depot Deals'

server = app.server

stores_worker = Worker(HOME_DEPOT_STORES_WORKER_ID)
search_worker = Worker(HOME_DEPOT_SEARCH_WORKER_ID)

INITIAL_LATITUDE = '38.13591366397597'
INITIAL_LONGITUDE = '-96.72647129706326'

HOME_DEPOT_MAIN_CATEGORIES = [
    {'label': 'Appliances', 'value': '553460'},
    {'label': 'Bath & Faucets', 'value': '558975'},
    {'label': 'Blinds & Decor', 'value': '501728'},
    {'label': 'Building Materials', 'value': '501112'},
    {'label': 'Cleaning', 'value': '547938'},
    {'label': 'Decor', 'value': '503089'},
    {'label': 'Doors & Windows', 'value': '500921'},
    {'label': 'Electrical', 'value': '501997'},
    {'label': 'Flooring & Area Rugs', 'value': '500535'},
    {'label': 'Furniture', 'value': '569856'},
    {'label': 'Hardware', 'value': '562522'},
    {'label': 'Heating & Cooling', 'value': '565784'},
    {'label': 'Holiday', 'value': '530294'},
    {'label': 'Kitchen', 'value': '501714'},
    {'label': 'Lighting & Ceiling Fans', 'value': '554225'},
    {'label': 'Lumber & Composites', 'value': '547828'},
    {'label': 'Outdoors', 'value': '556274'},
    {'label': 'Paint', 'value': '501637'},
    {'label': 'Plumbing', 'value': '547448'},
    {'label': 'Smart Home', 'value': '561884'},
    {'label': 'Storage & Organization', 'value': '503114'}
]

PRESET_STORES = [
    {'label': 'New York, NY - Manhattan West 23rd St - #6175', 'value': '6175'},
    {'label': 'Los Angeles, CA - Hyde Park - #1039', 'value': '1039'},
    {'label': 'Chicago, IL - South Loop - #1950', 'value': '1950'},
    {'label': 'Houston, TX - Brinkman - #0577', 'value': '0577'},
    {'label': 'Phoenix, AZ - Thomas Rd - #0477', 'value': '0477'},
    {'label': 'Philadelphia, PA - S Philadelphia - #4101', 'value': '4101'},
    {'label': 'Jacksonville, FL - Jacksonville (lane Ave) - #6346', 'value': '6346'},
    {'label': 'Columbus, OH - West Broad - #3819', 'value': '3819'}
]

STORE_LOCATIONS = {
    '6175': {
        'lat': '40.741983',
        'lon': '-73.990877'
    },
    '1039': {
        'lat': '33.987317',
        'lon': '-118.312092'
    },
    '1950': {
        'lat': '41.865722',
        'lon': '-87.641322'
    },
    '0577': {
        'lat': '29.81123',
        'lon': '-95.417796'
    },
    '0477': {
        'lat': '33.478746',
        'lon': '-112.0033'
    },
    '4101': {
        'lat': '39.92591',
        'lon': '-75.143004'
    },
    '6346': {
        'lat': '30.310197',
        'lon': '-81.749904'
    },
    '3819': {
        'lat': '39.949139',
        'lon': '-83.121624'
    }
}

app.layout = html.Div(children=[
    html.H1(children='Home Depot Cheapo', className='text-center'),

    html.P(children='Find discounted items in stock at your local store', className='text-center'),

    html.Div([
        html.Div([
            html.Label('Keyword or Item ID'),
            dcc.Input(value='', type='text', id='input-keyword', style={'width': '100%'})
        ], className='col-md-6'),
        html.Div([
            html.Label('Category'),
            dcc.Dropdown(
                id='input-category',
                options=HOME_DEPOT_MAIN_CATEGORIES
            )
        ], className='col-md-6')
    ], className='row'),

    html.Div([
        html.Div([
            html.Label('Home Depot Store'),
            dcc.Dropdown(
                id='input-selected-store',
                options=PRESET_STORES,
                className='mb-3'
            ),
            dcc.Graph(id='graph-stores')
        ], className='col')
    ], className='row'),

    html.Div([
        html.Div([
            html.Button(id='button-submit', n_clicks_timestamp=0, children='Find Discounts', className='btn-block btn-success')
        ], className='col')
    ], className='row mt-3'),

    html.Div([
        html.Div('', id='output-results'),
        html.Div([
            html.Div([
                html.Span('Page '),
                html.Span('', id='state-current-page'),
                html.Span(' of '),
                html.Span('', id='state-total-pages')
            ]),
            html.Button(id='button-back', n_clicks_timestamp=0, children='Back', className='mr-3'),
            html.Button(id='button-next', n_clicks_timestamp=0, children='Next')
        ], className='text-center')
    ], id='container-results', className='mb-3', style={'display': 'none'}),

    html.Div('Please enter a keyword and/or category', id='error-no-inputs', className='alert alert-danger text-center mt-3', style={'display': 'none'}),

    html.Div(id='data-results', style={'display': 'none'})

], className='container-fluid')

@app.callback(
    Output('graph-stores', 'relayoutData'),
    [Input('input-selected-store', 'value')])
def go_to_stores(input_store_id):
    if input_store_id:
        return {
            'mapbox.center': {
                'lat': STORE_LOCATIONS[input_store_id]['lat'],
                'lon': STORE_LOCATIONS[input_store_id]['lon']
            },
            'mapbox.zoom': 9
        }

@app.callback(
    Output('input-selected-store', 'options'),
    [Input('graph-stores', 'figure')])
def populate_input_stores(figure_data):
    stores = []
    store_ids = []
    for label in figure_data['data'][0]['text']:
        store_id = label.split('#')[-1]
        stores.append({
            'label': label,
            'value': store_id
        })
        store_ids.append(store_id)

    return stores + [store for store in PRESET_STORES if store['value'] not in store_ids]

@app.callback(
    Output('graph-stores', 'figure'),
    [Input('graph-stores', 'relayoutData')])
def pan_store_map(layout_data):
    latitude = INITIAL_LATITUDE
    longitude = INITIAL_LONGITUDE
    map_zoom = 3

    stores = []

    if layout_data and 'mapbox.center' in layout_data:
        latitude = str(layout_data['mapbox.center']['lat'])
        longitude = str(layout_data['mapbox.center']['lon'])
        map_zoom = layout_data['mapbox.zoom']

        store_results = stores_worker.run({
            'latitude': latitude,
            'longitude': longitude},
            saveResults=False)

        stores = json.loads(store_results['item']['taskResults'][0]['responseText']).get('stores', [])

    lats = []
    lngs = []
    texts = []

    for obj in stores:
        store_id = obj['storeId']

        store_label = obj['address']['city'] + ', ' + obj['address']['state'] + ' - ' + obj['name'] + ' - #' + store_id

        lats.append(obj['coordinates']['lat'])
        lngs.append(obj['coordinates']['lng'])
        texts.append(store_label)

        STORE_LOCATIONS[store_id] = {
            'lat': obj['coordinates']['lat'],
            'lon': obj['coordinates']['lng']
        }

    data = [
        go.Scattermapbox(
            lat=lats,
            lon=lngs,
            mode='markers',
            marker=dict(
                size=14
            ),
            text=texts)]

    layout = go.Layout(
        autosize=True,
        height=300,
        hovermode='closest',
        showlegend=False,
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=0,
            pad=0
        ),
        mapbox=dict(
            accesstoken=PUBLIC_MAPBOX_TOKEN,
            bearing=0,
            center=dict(
                lat=float(latitude),
                lon=float(longitude)
            ),
            pitch=0,
            zoom=map_zoom
        )
    )

    fig = dict(data=data, layout=layout)
    return fig

@app.callback(
    Output('input-selected-store', 'value'),
    [Input('graph-stores', 'clickData')])
def select_store_map(click_data):
    if click_data:
        store_id = click_data['points'][0]['text'].split('#')[-1]
        return store_id

@app.callback(
    Output('state-current-page', 'children'),
    [Input('button-submit', 'n_clicks_timestamp'), Input('button-next', 'n_clicks_timestamp'), Input('button-back', 'n_clicks_timestamp')],
    [State('state-current-page', 'children'), State('state-total-pages', 'children')])
def update_current_page(submit_n_clicks_timestamp, next_n_clicks_timestamp, back_n_clicks_timestamp, current_page, total_pages):
    if submit_n_clicks_timestamp > next_n_clicks_timestamp and submit_n_clicks_timestamp > back_n_clicks_timestamp:
        return '1'
    elif next_n_clicks_timestamp > back_n_clicks_timestamp:
        return str(min(int(current_page) + 1, int(total_pages)))
    elif back_n_clicks_timestamp > 0:
        return str(max(int(current_page) - 1, 1))
    else:
        return ''

@app.callback(
    Output('data-results', 'children'),
    [Input('state-current-page', 'children')],
    [State('input-selected-store', 'value'), State('input-category', 'value'), State('input-keyword', 'value')])
def update_search_results(current_page, selected_store, category_id, search_term):
    if current_page:
        if not category_id and not search_term:
            return 'ERROR'
        store_id = selected_store.split('#')[-1] if isinstance(selected_store, str) else ''
        search_results = search_worker.run({
            'store_id': store_id,
            'category_id': category_id or '',
            'keyword': search_term,
            'start_index': str((int(current_page) - 1) * 48)},
            saveResults=False)
        return json.dumps(search_results)
    else:
        return ''

@app.callback(
    Output('container-results', 'style'),
    [Input('data-results', 'children')])
def show_results(results):
    if results and results != 'ERROR':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('error-no-inputs', 'style'),
    [Input('data-results', 'children')])
def show_error(results):
    if results == 'ERROR':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('state-total-pages', 'children'),
    [Input('data-results', 'children')])
def update_total_pages(results):
    if results and results != 'ERROR':
        results_obj = json.loads(results)
        total_results = json.loads(results_obj['item']['taskResults'][0]['responseText'])['searchReport']['totalProducts']
        total_pages = max(1, math.ceil(total_results / 48))
        return str(total_pages)
    else:
        return ''

@app.callback(
    Output('output-results', 'children'),
    [Input('data-results', 'children')],
    [State('input-selected-store', 'value')])
def display_click_data(results, store_id):
    if results and results != 'ERROR':
        results_obj = json.loads(results)

        total_results = json.loads(results_obj['item']['taskResults'][0]['responseText'])['searchReport']['totalProducts']
        if total_results == 0:
            return html.Div('Sorry, no results were returned', className='alert alert-danger text-center mt-3')

        all_products = json.loads(results_obj['item']['taskResults'][0]['responseText']).get('skus', [])
        on_sale_products = [ product for product in all_products if product['storeSku'].get('pricing', {'percentageOff': 0})['percentageOff'] > 0 ]

        html_arr = []
        for item in on_sale_products:
            inventory = 'Not in Store' if store_id else ''
            if 'inventory' in item['storeSku'] and item['storeSku']['inventory'][0]['sellableQty'] > 0:
                inventory = str(item['storeSku']['inventory'][0]['sellableQty']) + ' in Store'

            html_arr.append(
                html.Div([
                    html.Div([
                        html.Img(src=item['info']['imageUrl'].replace('<SIZE>', '100'), className='float-left mr-3 img-thumbnail'),
                        html.A(item['info'].get('brandName', '') + ' - ' + item['info']['productLabel'], href='https://homedepot.com/' + item['productUrl'], target='_blank'),
                        html.Div(['$' + str(item['storeSku']['pricing']['specialPrice']) + ' (' + str(item['storeSku']['pricing']['percentageOff']) + '% Off)']),
                        html.Div(['Item ID: ' + str(item['itemId'])]),
                        html.Div(inventory)
                    ], className='card-body')
                ], className='card mt-3 mb-3'))

        if html_arr:
            return html_arr
        else:
            return html.Div('No discounts in these results, try the next page', className='alert alert-warning text-center mt-3')
    else:
        return ''

external_css = [
    # Normalize the CSS
    'https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css',
    # # Fonts
    'https://fonts.googleapis.com/css?family=Open+Sans|Roboto',
    'https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css',
    # Bootstrap
    'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
    # Dash Layout
    'https://cdn.rawgit.com/xhlulu/0acba79000a3fd1e6f552ed82edb8a64/raw/dash_template.css',
    'https://stevesie-assets.nyc3.digitaloceanspaces.com/dash-styles.css'
]

for css in external_css:
    app.css.append_css({'external_url': css})

if __name__ == '__main__':
    app.run_server(debug=True)
