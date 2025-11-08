
import streamlit as st
import pandas as pd
import plotly.graph_objects as go  # <-- IMPORT PLOTLY
from scipy.optimize import curve_fit
from scipy.stats import linregress
import numpy as np
import io

# --- 1. Page Setup ---
st.set_page_config(
    page_title="Enzyme Kinetics Analyzer",
    layout="wide"
)
st.title("🧪 Enzyme Kinetics Analyzer")
st.subheader("Michaelis-Menten vs. Lineweaver-Burk")
st.write("Upload your data to see both non-linear and linear fits.")

# --- 2. Define Units (as a sidebar input) ---
st.sidebar.header("Settings")
S_units = st.sidebar.text_input("Substrate Units", "mM")
v_units = st.sidebar.text_input("Velocity Units", "μM/min")

# --- 3. File Uploader ---
uploaded_file = st.file_uploader("Upload your .csv data file")

# --- 4. Main Analysis ---
if uploaded_file is not None:
    
    try:
        data = pd.read_csv(uploaded_file)
        S = data['Substrate_Concentration']
        v = data['Initial_Velocity']
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.warning("Please ensure your file has columns: 'Substrate_Concentration' and 'Initial_Velocity'")
        st.stop()

    # --- Analysis Logic (Unchanged) ---
    
    # 3.A. Non-linear Fit
    def michaelis_menten(S, Vmax, Km):
        return (Vmax * S) / (Km + S)
    
    try:
        initial_guesses = [max(v), np.median(S)]
        params, covariance = curve_fit(michaelis_menten, S, v, p0=initial_guesses)
        Vmax_fit = params[0]
        Km_fit = params[1]

        # 3.B. Linear Fit
        inv_S = 1 / S
        inv_v = 1 / v
        regression = linregress(inv_S, inv_v)
        slope = regression.slope
        intercept = regression.intercept
        Vmax_lb = 1 / intercept
        Km_lb = slope * Vmax_lb
        x_intercept_val = -1 / Km_lb
    except Exception as e:
        st.error(f"Error during data fitting: {e}")
        st.warning("Could not calculate kinetics. Check your data for outliers or zero values.")
        st.stop()


    # --- 5. Display Results (Unchanged) ---
    st.header("📊 Results")
    col1, col2 = st.columns(2) 

    with col1:
        st.subheader("Method 1: Non-linear M-M")
        st.metric(label=f"Vmax ({v_units})", value=f"{Vmax_fit:.2f}")
        st.metric(label=f"Km ({S_units})", value=f"{Km_fit:.2f}")

    with col2:
        st.subheader("Method 2: Linear L-B")
        st.metric(label=f"Vmax ({v_units})", value=f"{Vmax_lb:.2f}")
        st.metric(label=f"Km ({S_units})", value=f"{Km_lb:.2f}")

    st.header("📈 Plots")
    
    # Use columns to show plots side-by-side
    fig_col1, fig_col2 = st.columns(2)

    with fig_col1:
        # === (NEW) Plot 1: Interactive Michaelis-Menten Plot ===
        
        # Create the plot figure
        fig1 = go.Figure()

        # Add the raw data points
        fig1.add_trace(go.Scatter(
            x=S, y=v, 
            mode='markers', 
            name='Experimental Data',
            marker=dict(color='red', size=8)
        ))
        
        # Add the fitted line
        S_fit = np.linspace(0, max(S), 100)
        v_fit = michaelis_menten(S_fit, Vmax_fit, Km_fit)
        fig1.add_trace(go.Scatter(
            x=S_fit, y=v_fit,
            mode='lines',
            name='Michaelis-Menten Fit',
            line=dict(color='blue')
        ))
        
        # Update layout
        fig1.update_layout(
            title='Michaelis-Menten Fit',
            xaxis_title=f'Substrate Concentration [S] ({S_units})',
            yaxis_title=f'Initial Velocity (v) ({v_units})',
            legend_title="Legend"
        )
        
        # Display with Streamlit
        st.plotly_chart(fig1, use_container_width=True)


    with fig_col2:
        # === (NEW) Plot 2: Interactive Lineweaver-Burk Plot ===
        
        fig2 = go.Figure()
        
        # Add the transformed data points
        fig2.add_trace(go.Scatter(
            x=inv_S, y=inv_v,
            mode='markers',
            name='Transformed Data',
            marker=dict(color='purple', size=8)
        ))
        
        # Add the fitted line
        x_fit = np.linspace(min(0, x_intercept_val * 1.1), max(inv_S) * 1.1, 100)
        y_fit = slope * x_fit + intercept
        fig2.add_trace(go.Scatter(
            x=x_fit, y=y_fit,
            mode='lines',
            name='Linear Fit',
            line=dict(color='green')
        ))
        
        # Update layout
        fig2.update_layout(
            title='Lineweaver-Burk Fit',
            xaxis_title=f'1 / [S]   (1 / {S_units})',
            yaxis_title=f'1 / v   (1 / {v_units})',
            legend_title="Legend"
        )
        
        # Add the 0,0 lines
        fig2.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        fig2.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        
        # Display with Streamlit
        st.plotly_chart(fig2, use_container_width=True)


# --- Add a "how to" guide at the bottom (Unchanged) ---
st.header("How to Use")
st.markdown("""
1.  **Prepare your data**: Create a `.csv` file with two columns: `Substrate_Concentration` and `Initial_Velocity`.
2.  **Upload**: Click the 'Browse files' button or drag your file onto the uploader.
3.  **Analyze**: The app will automatically update with your results and plots.
4.  **Settings**: Use the sidebar to change the units that are displayed on the plots.
""")
