import streamlit as st
import pandas as pd
from room_allocation_system import HostelAllocationSystem
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Hostel Room Allocation System",
    page_icon="🏢",
    layout="wide"
)

# Initialize session state
if 'system' not in st.session_state:
    st.session_state.system = HostelAllocationSystem()

if 'allocation_results' not in st.session_state:
    st.session_state.allocation_results = []

# Custom CSS for better styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    .allocation-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .allocation-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏢 Hostel Room Allocation System")
st.markdown("---")

# Sidebar for system controls
with st.sidebar:
    st.header("System Controls")
    
    if st.button("🔄 Reset All Allocations", type="secondary", use_container_width=True):
        st.session_state.system.reset_allocations()
        st.session_state.allocation_results = []
        st.success("All allocations have been reset!")
    
    st.markdown("---")
    
    # Save/Load functionality
    st.subheader("Save/Load State")
    
    # Save state
    save_filename = st.text_input("Filename to save", value="hostel_state.json")
    if st.button("💾 Save Current State", use_container_width=True):
        try:
            st.session_state.system.save_state(save_filename)
            st.success(f"State saved to {save_filename}")
        except Exception as e:
            st.error(f"Error saving state: {e}")
    
    # Load state
    uploaded_file = st.file_uploader("Load state from file", type=['json'])
    if uploaded_file is not None:
        try:
            state_data = json.load(uploaded_file)
            # Create a temporary file to load from
            temp_filename = "temp_state.json"
            with open(temp_filename, 'w') as f:
                json.dump(state_data, f)
            st.session_state.system.load_state(temp_filename)
            st.success("State loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading state: {e}")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Allocate Rooms", "📊 Hostel Status", "📋 Allocation History", "🏗️ Building Layout"])

# Tab 1: Room Allocation
with tab1:
    st.header("Allocate Rooms for Student Groups")
    st.info("📌 **Note**: Enter one roll number per room. Each student has already chosen their roommate.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Group Information")
        
        # Input method selection
        input_method = st.radio("Input Method", ["Manual Entry", "Paste List"])
        
        if input_method == "Manual Entry":
            group_size = st.number_input("Number of Rooms Needed", min_value=1, max_value=15, value=4, 
                                       help="Maximum 15 rooms per group")
            
            # Generate sample roll numbers for testing
            if st.checkbox("Use sample roll numbers for testing"):
                roll_numbers = [f"R{i:03d}" for i in range(1, group_size + 1)]
                roll_numbers_input = ", ".join(roll_numbers)
            else:
                roll_numbers_input = st.text_area(
                    "Enter Roll Numbers (one per room, comma-separated)",
                    placeholder="R001, R002, R003, R004",
                    height=100,
                    help="Enter one representative roll number for each room"
                )
        else:
            roll_numbers_text = st.text_area(
                "Paste Roll Numbers (one per line, one per room)",
                placeholder="R001\nR002\nR003\nR004",
                height=200,
                help="Enter one representative roll number for each room"
            )
            if roll_numbers_text:
                roll_numbers = [r.strip() for r in roll_numbers_text.split('\n') if r.strip()]
                group_size = len(roll_numbers)
                roll_numbers_input = ", ".join(roll_numbers)
            else:
                group_size = 0
                roll_numbers_input = ""
        
        st.markdown(f"**Total Students**: {group_size * 2} (in {group_size} rooms)")
        
        # Allocation button
        if st.button("🏠 Allocate Rooms", type="primary", use_container_width=True):
            if roll_numbers_input:
                try:
                    roll_numbers = [r.strip() for r in roll_numbers_input.split(',') if r.strip()]
                    
                    if len(roll_numbers) != group_size:
                        st.error(f"Number of roll numbers ({len(roll_numbers)}) doesn't match number of rooms ({group_size})")
                    else:
                        allocation = st.session_state.system.allocate_rooms(group_size, roll_numbers)
                        
                        # Store result for history
                        result = {
                            'timestamp': datetime.now(),
                            'group_size': group_size,
                            'allocation': allocation
                        }
                        st.session_state.allocation_results.append(result)
                        
                        st.success(f"✅ {group_size} rooms allocated successfully for {group_size * 2} students!")
                        
                except Exception as e:
                    st.error(f"❌ Allocation failed: {e}")
            else:
                st.error("Please enter roll numbers")
    
    with col2:
        st.subheader("Latest Allocation Result")
        
        if st.session_state.allocation_results:
            latest_result = st.session_state.allocation_results[-1]
            
            # Create allocation dataframe
            allocation_data = []
            for roll, room in latest_result['allocation'].items():
                building = room[0]
                floor = room[:2]
                room_num = room.split('-')[1]
                allocation_data.append({
                    'Roll Number': roll,
                    'Building': building,
                    'Floor': floor,
                    'Room': room_num,
                    'Full Room ID': room
                })
            
            df = pd.DataFrame(allocation_data)
            
            # Display summary
            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.metric("Rooms Allocated", len(df))
            with col2_2:
                st.metric("Students Accommodated", len(df) * 2)
            with col2_3:
                st.metric("Floors Used", df['Floor'].nunique())
            
            # Display allocation table
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download button for allocation
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Allocation as CSV",
                data=csv,
                file_name=f"allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Tab 2: Hostel Status
with tab2:
    st.header("Current Hostel Status")
    
    status = st.session_state.system.get_hostel_status()
    
    # Overall statistics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Rooms", status['total_rooms'])
    with col2:
        st.metric("Occupied Rooms", status['occupied_rooms'])
    with col3:
        st.metric("Available Rooms", status['available_rooms'])
    with col4:
        st.metric("Total Slots", status['total_slots'])
    with col5:
        st.metric("Occupied Slots", status['occupied_slots'])
    with col6:
        st.metric("Available Slots", status['available_slots'])
    
    # Download complete allocation list
    st.subheader("📥 Download Complete Allocation List")
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        # Generate complete allocation list
        complete_allocation = []
        for building_name, building in st.session_state.system.buildings.items():
            for floor_name, floor in building.items():
                for room in floor.rooms:
                    if len(room.occupied_by) > 0:
                        # Get the representative student (first one)
                        representative = room.occupied_by[0]
                        if not representative.endswith('_roommate'):
                            complete_allocation.append({
                                'Roll Number': representative,
                                'Room Number': room.room_id,
                                'Building': building_name,
                                'Floor': floor_name
                            })
        
        if complete_allocation:
            complete_df = pd.DataFrame(complete_allocation)
            complete_df = complete_df.sort_values(['Building', 'Floor', 'Room Number'])
            
            csv_complete = complete_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Complete Allocation List (CSV)",
                data=csv_complete,
                file_name=f"complete_allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.info(f"Total allocated rooms: {len(complete_df)}")
        else:
            st.warning("No allocations have been made yet.")
    
    with col_download2:
        # Summary statistics
        if complete_allocation:
            st.markdown("**Allocation Summary:**")
            summary_df = pd.DataFrame(complete_allocation).groupby(['Building', 'Floor']).size().reset_index(name='Rooms Allocated')
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Occupancy visualization
    st.subheader("Occupancy Overview")
    
    # Create occupancy data for visualization
    occupancy_data = []
    for building_name, building in st.session_state.system.buildings.items():
        for floor_name, floor in building.items():
            occupancy_data.append({
                'Building': building_name,
                'Floor': floor_name,
                'Total Slots': len(floor.rooms) * 2,
                'Occupied Slots': sum(len(room.occupied_by) for room in floor.rooms),
                'Available Slots': floor.total_available_slots
            })
    
    occupancy_df = pd.DataFrame(occupancy_data)
    occupancy_df['Occupancy %'] = (occupancy_df['Occupied Slots'] / occupancy_df['Total Slots'] * 100).round(1)
    
    # Bar chart for occupancy
    fig = px.bar(occupancy_df, x='Floor', y='Occupancy %', 
                 color='Building', 
                 title='Floor-wise Occupancy Percentage',
                 labels={'Occupancy %': 'Occupancy Percentage'},
                 color_discrete_map={'A': '#1f77b4', 'B': '#ff7f0e'})
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed floor information
    st.subheader("Detailed Floor Information")
    
    building_select = st.selectbox("Select Building", ["A", "B"])
    
    building_data = st.session_state.system.buildings[building_select]
    
    for floor_name, floor in building_data.items():
        with st.expander(f"📍 {floor_name} - {floor.total_available_slots} slots available"):
            # Room grid visualization
            room_cols = st.columns(5)
            
            for idx, room in enumerate(floor.rooms):
                col_idx = idx % 5
                with room_cols[col_idx]:
                    if room.is_available:
                        if len(room.occupied_by) == 0:
                            st.success(f"🟢 {room.number}\n(Empty)")
                        else:
                            # Show only the representative student
                            representative = room.occupied_by[0]
                            if not representative.endswith('_roommate'):
                                st.warning(f"🟡 {room.number}\n({representative})")
                            else:
                                st.warning(f"🟡 {room.number}\n(Occupied)")
                    else:
                        st.error(f"🔴 {room.number}\n(Full)")

# Tab 3: Allocation History
with tab3:
    st.header("Allocation History")
    
    if st.session_state.system.allocation_history:
        # Convert history to dataframe
        history_data = []
        for idx, record in enumerate(st.session_state.system.allocation_history):
            timestamp = datetime.fromisoformat(record['timestamp'])
            history_data.append({
                'Index': idx + 1,
                'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Rooms Allocated': record['group_size'],
                'Students Accommodated': record['group_size'] * 2,
                'Representatives': ', '.join(record['allocation'].keys())
            })
        
        history_df = pd.DataFrame(history_data)
        
        # Display history table
        st.dataframe(history_df, use_container_width=True)
        
        # Select allocation to view details
        if st.checkbox("View allocation details"):
            selected_idx = st.selectbox("Select allocation", 
                                      options=range(len(st.session_state.system.allocation_history)),
                                      format_func=lambda x: f"Allocation {x+1} - {history_df.iloc[x]['Timestamp']}")
            
            selected_allocation = st.session_state.system.allocation_history[selected_idx]['allocation']
            
            # Display selected allocation
            allocation_detail = []
            for roll, room in selected_allocation.items():
                allocation_detail.append({'Representative Roll Number': roll, 'Room': room})
            
            detail_df = pd.DataFrame(allocation_detail)
            st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("No allocations have been made yet.")

# Tab 4: Building Layout
with tab4:
    st.header("Building Layout Reference")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Building A")
        st.markdown("""
        **4 Floors with scattered room numbers:**
        - **A0**: 001-005, 013-017, 022-026 (15 rooms)
        - **A1**: 101-105, 114-118, 122-126 (15 rooms)
        - **A2**: 201-205, 214-218, 221-225 (15 rooms)
        - **A3**: 301-305, 314-318, 319-323 (15 rooms)
        
        **Total**: 60 rooms, 120 student slots
        """)
        
    with col2:
        st.subheader("🏢 Building B")
        st.markdown("""
        **2 Floors with continuous room numbers:**
        - **B1**: 001-024 (24 rooms)
        - **B2**: 001-024 (24 rooms)
        
        **Total**: 48 rooms, 96 student slots
        """)
    
    st.markdown("---")
    st.markdown("""
    ### System Features:
    - ✅ **Fair & Random Allocation**: Groups are randomly assigned to available floors
    - ✅ **Group Cohesion**: Keeps groups together on the same floor when possible
    - ✅ **Smart Splitting**: Large groups are split logically when necessary
    - ✅ **Continuous Room Preference**: Allocates continuous rooms when available
    - ✅ **Real-time Tracking**: Automatically updates room availability
    - ✅ **State Persistence**: Save and load allocation states
    """)

# Footer
st.markdown("---")
st.markdown("🏢 Hostel Room Allocation System v1.0 | Built with Streamlit")
