# Save this file as "inhibition_app.py"
# In your terminal, run: streamlit run inhibition_app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
import io

# --- 1. Page Setup ---
st.set_page_config(
    page_title="Enzyme Inhibition Analyzer",
    layout="wide"
)
st.title("🔬 Enzyme Inhibition Analyzer")
st.subheader("Comparative Lineweaver-Burk Plot")

# --- 2. Define Units (as a sidebar input) ---
st.sidebar.header("Settings")
s_unit_options = ['mM', 'μM', 'M', 'nM']
v_unit_options = ['μM/min', 'μM/s', 'mM/min', 'mM/s', 'M/min', 'M/s', 'nM/min', 'nM/s']
S_units = st.sidebar.selectbox(
    "Substrate Units", 
    options=s_unit_options, 
    index=0
) 
v_units = st.sidebar.selectbox(
    "Velocity Units", 
    options=v_unit_options, 
    index=0
)

# --- 3. Data Entry ---
st.write("Paste your 3-column data from Excel/Sheets (must include headers):")

# Default data uses plain text headers, as this is what the user will paste
default_data = "Substrate_Concentration\tV0_Uninhibited\tV0_Inhibited\n" \
               "1\t17.1\t7.1\n" \
               "2\t29.5\t13.6\n" \
               "4\t51.2\t25.0\n" \
               "8\t73.9\t42.8\n" \
               "16\t102.1\t66.6\n" \
               "32\t118.5\t92.3\n" \
               "50\t130.2\t107.1"

data_string = st.text_area(
    "Paste Data Here",
    default_data,
    height=250,
    help="Copy and paste your 3-column table directly from Excel or Sheets."
)


# --- 4. Function to Process Data ---
def process_kinetics_data(df, velocity_column):
    try:
        S = df['Substrate_Concentration']
        v = df[velocity_column]
        
        non_zero_mask = S != 0
        S = S[non_zero_mask]
        v = v[non_zero_mask]
        
        inv_S, inv_v = 1 / S, 1 / v
        regression = linregress(inv_S, inv_v)
        Vmax = 1 / regression.intercept
        Km = regression.slope * Vmax
        return inv_S, inv_v, Vmax, Km, regression
    except Exception as e:
        st.error(f"Error processing {velocity_column}: {e}")
        return None


# --- 5. Main Analysis ---
if data_string:
    
    try:
        data_file_object = io.StringIO(data_string)
        data = pd.read_csv(data_file_object, sep=None, engine='python')
        
        # Plain text headers for code
        required_cols = ['Substrate_Concentration', 'V0_Uninhibited', 'V0_Inhibited']
        # LaTeX headers for display
        required_cols_display = ['Substrate_Concentration', '$V_0$_Uninhibited', '$V_0$_Inhibited'] # <-- MODIFIED
        
        if not all(col in data.columns for col in required_cols):
            st.error(f"Error: Your data must have these 3 columns: {required_cols_display}") # <-- MODIFIED
            st.stop()
            
    except Exception as e:
        st.error(f"Error reading data: {e}")
        st.warning("Please make sure you paste the 3-column table, *including* the headers.")
        st.stop()

    # Process both datasets from the single DataFrame
    processed_un = process_kinetics_data(data, "V0_Uninhibited")
    processed_in = process_kinetics_data(data, "V0_Inhibited")
    
    if processed_un and processed_in:
        inv_S_un, inv_v_un, Vmax_un, Km_un, reg_un = processed_un
        inv_S_in, inv_v_in, Vmax_in, Km_in, reg_in = processed_in

        # --- 6. Display Results ---
        st.header("📊 Results")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.subheader("Uninhibited (Control)")
            st.metric(label=f"Vmax ({v_units})", value=f"{Vmax_un:.2f}")
            st.metric(label=f"Km ({S_units})", value=f"{Km_un:.2f}")
        with res_col2:
            st.subheader("Inhibited")
            st.metric(label=f"Vmax ({v_units})", value=f"{Vmax_in:.2f}")
            st.metric(label=f"Km ({S_units})", value=f"{Km_in:.2f}")

        # --- 7. Display Interactive Plot ---
        st.header("📈 Comparative Lineweaver-Burk Plot")
        
        fig = go.Figure()

        x_int_un = -1 / Km_un
        x_int_in = -1 / Km_in
        max_x = max(max(inv_S_un), max(inv_S_in)) * 1.1
        min_x = min(0, x_int_un, x_int_in) * 1.1 
        x_fit = np.linspace(min_x, max_x, 100)
        
        # Uninhibited Traces
        fig.add_trace(go.Scatter(
            x=inv_S_un, y=inv_v_un, mode='markers', name='Uninhibited (Data)',
            marker=dict(color='blue', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=x_fit, y=(reg_un.slope * x_fit + reg_un.intercept), mode='lines', 
            name=f'Uninhibited Fit (Vmax={Vmax_un:.1f}, Km={Km_un:.1f})',
            line=dict(color='blue')
        ))
        
        # Inhibited Traces
        fig.add_trace(go.Scatter(
            x=inv_S_in, y=inv_v_in, mode='markers', name='Inhibited (Data)',
            marker=dict(color='red', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=x_fit, y=(reg_in.slope * x_fit + reg_in.intercept), mode='lines',
            name=f'Inhibited Fit (Vmax={Vmax_in:.1f}, Km={Km_in:.1f})',
            line=dict(color='red')
        ))

        # Layout
        fig.update_layout(
            title='Inhibition Analysis',
            xaxis_title=f'1 / [S]   (1 / {S_units})',
            yaxis_title=f'1 / v   (1 / {v_units})',
            legend_title="Legend"
        )
        fig.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        
        st.plotly_chart(fig, use_container_width=True)

# --- (MODIFIED) 8. Instructions ---
st.header("How to Use")
st.markdown("""
1.  **Prepare your data**: In Excel/Sheets, make sure you have 3 columns: `Substrate_Concentration`, `$V_0$_Uninhibited`, `$V_0$_Inhibited`.
2.  **Copy**: Select all 3 columns (including the headers).
3.  **Paste**: Paste the entire table into the text box above, replacing the sample data.
4.  **Analyze**: The app will automatically update.
5.  **Settings**: Use the sidebar to change the units.
""")
