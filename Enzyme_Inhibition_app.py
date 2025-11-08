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
S_units = st.sidebar.text_input("Substrate Units", "mM")
v_units = st.sidebar.text_input("Velocity Units", "μM/min")

# --- 3. File Uploaders ---
st.write("Upload both your uninhibited (control) and inhibited data files.")
col1, col2 = st.columns(2)
with col1:
    file_un = st.file_uploader("Upload Uninhibited .csv", type="csv")
with col2:
    file_in = st.file_uploader("Upload Inhibited .csv", type="csv")

# --- 4. Function to Process Data ---
# This is our reusable function from the original script
def process_kinetics_data(uploaded_file):
    try:
        data = pd.read_csv(uploaded_file)
        S, v = data['Substrate_Concentration'], data['Initial_Velocity']
        
        # Filter out any S=0 data to avoid divide-by-zero
        non_zero_mask = S != 0
        S = S[non_zero_mask]
        v = v[non_zero_mask]
        
        inv_S, inv_v = 1 / S, 1 / v
        regression = linregress(inv_S, inv_v)
        Vmax = 1 / regression.intercept
        Km = regression.slope * Vmax
        
        # Return all the useful values
        return inv_S, inv_v, Vmax, Km, regression
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {e}")
        st.warning("Please ensure files have 'Substrate_Concentration' and 'Initial_Velocity' columns.")
        return None

# --- 5. Main Analysis ---
# Only run if BOTH files are uploaded
if file_un is not None and file_in is not None:
    
    # Process both datasets
    processed_un = process_kinetics_data(file_un)
    processed_in = process_kinetics_data(file_in)
    
    # Only proceed if both files were processed successfully
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

        # Generate X-values for the fit lines
        max_x = max(max(inv_S_un), max(inv_S_in)) * 1.1
        x_fit = np.linspace(0, max_x, 100)
        
        # --- Uninhibited Traces ---
        fig.add_trace(go.Scatter(
            x=inv_S_un, y=inv_v_un, mode='markers', name='Uninhibited (Data)',
            marker=dict(color='blue', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=x_fit, y=(reg_un.slope * x_fit + reg_un.intercept), mode='lines', 
            name=f'Uninhibited Fit (Vmax={Vmax_un:.1f}, Km={Km_un:.1f})',
            line=dict(color='blue')
        ))
        
        # --- Inhibited Traces ---
        fig.add_trace(go.Scatter(
            x=inv_S_in, y=inv_v_in, mode='markers', name='Inhibited (Data)',
            marker=dict(color='red', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=x_fit, y=(reg_in.slope * x_fit + reg_in.intercept), mode='lines',
            name=f'Inhibited Fit (Vmax={Vmax_in:.1f}, Km={Km_in:.1f})',
            line=dict(color='red')
        ))

        # --- Layout ---
        fig.update_layout(
            title='Inhibition Analysis',
            xaxis_title=f'1 / [S]   (1 / {S_units})',
            yaxis_title=f'1 / v   (1 / {v_units})',
            legend_title="Legend"
        )
        fig.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        
        st.plotly_chart(fig, use_container_width=True)

# --- 8. Instructions ---
st.header("How to Use")
st.markdown("""
1.  **Prepare your data**: Create two `.csv` files (one for uninhibited, one for inhibited).
2.  **Check headers**: Ensure both files have `Substrate_Concentration` and `Initial_Velocity` columns.
3.  **Upload**: Drag and drop both files into their respective upload boxes.
4.  **Analyze**: The app will automatically update with your comparative results and plots.
""")
