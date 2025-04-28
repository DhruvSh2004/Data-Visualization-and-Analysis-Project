import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk
import os
import io

class IndianEconomyDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Indian Economy Dashboard")
        self.root.state('zoomed')
        self.root.configure(bg="#f0f0f0")
        
        # Initialize theme state
        self.is_dark_theme = False
        self.light_theme = {
            'sidebar_bg': '#2c3e50', 'sidebar_fg': 'white',
            'content_bg': '#f0f0f0', 'chart_bg': 'white',
            'button_bg': '#34495e', 'button_fg': 'white',
            'header_bg': '#3498db', 'header_fg': 'white'
        }
        self.dark_theme = {
            'sidebar_bg': '#1a1a1a', 'sidebar_fg': '#cccccc',
            'content_bg': '#2e2e2e', 'chart_bg': '#3c3c3c',
            'button_bg': '#4a4a4a', 'button_fg': '#cccccc',
            'header_bg': '#1e88e5', 'header_fg': '#cccccc'
        }
        
        try:
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            root.destroy()
            return
            
        self.current_chart = None
        self.canvas = None
        
        self.setup_ui()
        
    def load_data(self):
        """Load and preprocess the datasets"""
        # Load indianEco.csv
        try:
            self.econ_data = pd.read_csv('indianEco.csv')
            self.econ_data.columns = self.econ_data.columns.str.strip()
            for col in self.econ_data.columns:
                if col != 'Country Name':
                    self.econ_data[col] = pd.to_numeric(self.econ_data[col], errors='coerce')
        except FileNotFoundError:
            raise FileNotFoundError("indianEco.csv not found in the project directory")
        
        # Load tax data
        try:
            self.tax_data = pd.read_csv('syb-18-chapter_6_direct_indirect_taxes_table_6.11.csv')
            self.tax_data['Year'] = self.tax_data['Year'].str.split('-').str[0].astype(int)
            for col in self.tax_data.columns:
                if col != 'Year':
                    self.tax_data[col] = pd.to_numeric(self.tax_data[col], errors='coerce')
        except FileNotFoundError:
            raise FileNotFoundError("syb-18-chapter_6_direct_indirect_taxes_table_6.11.csv not found in the project directory")
        
        # Load inflation data
        try:
            self.inflation_data = pd.read_csv('India_Inflation_Rate.csv')
            self.inflation_data = self.inflation_data.rename(columns={
                'year': 'Year',
                'Inflation_Rate': 'Inflation Rate (%)',
                'Annual_percent_geowth': 'Inflation Growth Rate (%)'
            })
            self.inflation_data['Inflation Rate (%)'] = self.inflation_data['Inflation Rate (%)'].str.rstrip('%').astype(float)
            self.inflation_data['Inflation Growth Rate (%)'] = self.inflation_data['Inflation Growth Rate (%)'].str.rstrip('%').astype(float)
            if 'Unnamed: 0' in self.inflation_data.columns:
                self.inflation_data = self.inflation_data.drop(columns=['Unnamed: 0'])
        except FileNotFoundError:
            raise FileNotFoundError("India_Inflation_Rate.csv not found in the project directory")
        
        # Load government debt data
        try:
            self.debt_data = pd.read_csv('India_Government_Debt.csv')
            self.debt_data = self.debt_data.rename(columns={
                'year': 'Year',
                'Government_Debt_as_percent_of_GDP': 'Government Debt (% of GDP)',
                'Annual_percent_geowth': 'Debt Growth Rate (%)'
            })
            self.debt_data['Government Debt (% of GDP)'] = self.debt_data['Government Debt (% of GDP)'].str.rstrip('%').astype(float)
            self.debt_data['Debt Growth Rate (%)'] = self.debt_data['Debt Growth Rate (%)'].str.rstrip('%').astype(float)
            if 'Unnamed: 0' in self.debt_data.columns:
                self.debt_data = self.debt_data.drop(columns=['Unnamed: 0'])
        except FileNotFoundError:
            raise FileNotFoundError("India_Government_Debt.csv not found in the project directory")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_theme = not self.is_dark_theme
        theme = self.dark_theme if self.is_dark_theme else self.light_theme
        
        # Update sidebar
        self.sidebar_frame.configure(bg=theme['sidebar_bg'])
        for widget in self.sidebar_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=theme['sidebar_bg'], fg=theme['sidebar_fg'])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=theme['button_bg'], fg=theme['button_fg'],
                               activebackground=theme['header_bg'], activeforeground=theme['header_fg'])
        
        # Update content frame
        self.content_frame.configure(bg=theme['content_bg'])
        self.header_frame.configure(bg=theme['header_bg'])
        self.header_title.configure(bg=theme['header_bg'], fg=theme['header_fg'])
        self.chart_frame.configure(bg=theme['chart_bg'])
        
        # Update chart frame content
        for widget in self.chart_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=theme['chart_bg'])
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=theme['chart_bg'], fg=theme['sidebar_fg'])
                    elif isinstance(child, ttk.Combobox) or isinstance(child, tk.Entry):
                        child.configure(foreground=theme['sidebar_fg'])
        
    def setup_ui(self):
        """Set up the UI components"""
        self.sidebar_frame = tk.Frame(self.root, bg=self.light_theme['sidebar_bg'], width=250)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        title_label = tk.Label(self.sidebar_frame, text="Indian Economy\nDashboard", 
                             font=("Arial", 18, "bold"), bg=self.light_theme['sidebar_bg'], 
                             fg=self.light_theme['sidebar_fg'], pady=20)
        title_label.pack(fill=tk.X)
        
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        
        buttons_info = [
            ("GDP Overview", self.show_gdp_overview),
            ("Population & Life Expectancy", self.show_population_life_expectancy),
            ("Inflation Trends", self.show_inflation_trends),
            ("Import/Export Analysis", self.show_import_export),
            ("Tax Revenue Analysis", self.show_tax_analysis),
            ("Government Debt Analysis", self.show_government_debt),
            ("Economic Growth Indicators", self.show_growth_indicators),
            ("Compare Indicators", self.show_compare_indicators),
            ("Data Table View", self.show_data_table)
        ]
        
        button_style = {
            "font": ("Arial", 12), "bg": self.light_theme['button_bg'], 
            "fg": self.light_theme['button_fg'], 
            "activebackground": self.light_theme['header_bg'], 
            "activeforeground": self.light_theme['header_fg'],
            "bd": 0, "padx": 10, "pady": 8, "width": 25
        }
        
        for btn_text, btn_command in buttons_info:
            btn = tk.Button(self.sidebar_frame, text=btn_text, command=btn_command, **button_style)
            btn.pack(fill=tk.X, padx=10, pady=5)
            
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        
        export_btn = tk.Button(self.sidebar_frame, text="Export Current Chart", 
                             command=self.export_chart, **button_style)
        export_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Widget 1: Theme Toggle Button
        theme_btn = tk.Button(self.sidebar_frame, text="Toggle Dark/Light Theme", 
                            command=self.toggle_theme, **button_style)
        theme_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.content_frame = tk.Frame(self.root, bg=self.light_theme['content_bg'])
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.header_frame = tk.Frame(self.content_frame, bg=self.light_theme['header_bg'], height=60)
        self.header_frame.pack(fill=tk.X)
        
        self.header_title = tk.Label(self.header_frame, 
                                   text="Welcome to Indian Economy Dashboard", 
                                   font=("Arial", 16, "bold"), 
                                   bg=self.light_theme['header_bg'], 
                                   fg=self.light_theme['header_fg'], pady=10)
        self.header_title.pack(side=tk.LEFT, padx=20)
        
        self.chart_frame = tk.Frame(self.content_frame, bg=self.light_theme['chart_bg'])
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        welcome_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_msg = tk.Label(welcome_frame, 
                             text="Welcome to the Indian Economy Dashboard", 
                             font=("Arial", 24, "bold"), bg=self.light_theme['chart_bg'], 
                             fg="#2c3e50")
        welcome_msg.pack(pady=30)
        
        instructions = """
        This dashboard provides visualizations and analysis tools for exploring 
        Indian economic data from 1960 to 2022.
        
        Use the sidebar menu to navigate between different charts and analysis options.
        
        Key features:
        • GDP Overview - Analyze GDP trends over time
        • Population & Life Expectancy - Track demographic changes
        • Inflation Trends - Observe inflation patterns and growth rates
        • Import/Export Analysis - Examine trade metrics
        • Tax Revenue Analysis - Review taxation data
        • Government Debt Analysis - Explore debt-to-GDP trends
        • Economic Growth Indicators - Compare multiple economic indicators
        • Compare Indicators - Create custom comparisons
        • Data Table View - Explore the raw data
        
        Select any option from the sidebar to begin exploring the data.
        """
        
        instructions_label = tk.Label(welcome_frame, text=instructions, 
                                   font=("Arial", 12), bg=self.light_theme['chart_bg'], 
                                   fg="#34495e", justify=tk.LEFT)
        instructions_label.pack(pady=10)
        
    def clear_chart_frame(self):
        """Clear the chart frame for new content"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
            
    def update_header(self, title):
        """Update the header title"""
        self.header_title.config(text=title)
        
    def export_chart(self):
        """Export the current chart as an image"""
        if self.current_chart is None:
            messagebox.showwarning("Warning", "No chart available to export!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.current_chart.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Chart exported successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chart: {str(e)}")
                
    def show_gdp_overview(self):
        """Show GDP overview chart"""
        self.clear_chart_frame()
        self.update_header("GDP Overview (1960-2020)")
        
        # Initialize zoom state
        self.zoom_level = 1.0
        
        def update_gdp_plot():
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(self.econ_data['Year'], self.econ_data['GDP (current US$)'] / 1e9, 
                    marker='o', linestyle='-', color='#3498db', linewidth=2)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_xlabel('Year', fontsize=12, fontweight='bold')
            ax.set_ylabel('GDP (Billion US$)', fontsize=12, fontweight='bold')
            ax.set_title('India GDP Trend (1960-2020)', fontsize=14, fontweight='bold')
            ax.set_xticks(self.econ_data['Year'][::5])
            ax.tick_params(axis='both', labelsize=10)
            
            events = [
                (1991, "Economic Liberalization"),
                (2008, "Global Financial Crisis"),
                (2016, "Demonetization"),
                (2020, "COVID-19 Pandemic")
            ]
            
            for year, event in events:
                idx = self.econ_data[self.econ_data['Year'] == year].index
                if len(idx) > 0:
                    idx = idx[0]
                    gdp = self.econ_data.loc[idx, 'GDP (current US$)'] / 1e9
                    ax.annotate(event, xy=(year, gdp), xytext=(0, 20), 
                              textcoords='offset points', ha='center', va='bottom',
                              bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                              arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))
            
            ax2 = ax.twinx()
            ax2.plot(self.econ_data['Year'], self.econ_data['GDP per capita (current US$)'], 
                    marker='^', linestyle='--', color='#e74c3c', linewidth=2)
            ax2.set_ylabel('GDP per Capita (US$)', fontsize=12, fontweight='bold', color='#e74c3c')
            ax2.tick_params(axis='y', labelcolor='#e74c3c')
            
            # Apply zoom
            gdp_max = (self.econ_data['GDP (current US$)'] / 1e9).max()
            gdp_per_capita_max = self.econ_data['GDP per capita (current US$)'].max()
            ax.set_ylim(0, gdp_max / self.zoom_level)
            ax2.set_ylim(0, gdp_per_capita_max / self.zoom_level)
            
            ax.legend(['GDP (Billion US$)', 'GDP per Capita (US$)'], loc='upper left')
            plt.tight_layout()
            
            self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.current_chart = fig
        
        # Widget 6: Zoom Control Buttons
        control_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        control_frame.pack(fill=tk.X, pady=10)
        
        def zoom_in():
            self.zoom_level = max(0.5, self.zoom_level * 0.8)
            update_gdp_plot()
        
        def zoom_out():
            self.zoom_level = min(2.0, self.zoom_level * 1.2)
            update_gdp_plot()
        
        zoom_in_btn = tk.Button(control_frame, text="Zoom In", command=zoom_in,
                               font=("Arial", 11), bg="#3498db", fg="white",
                               activebackground="#2980b9", activeforeground="white")
        zoom_in_btn.pack(side=tk.LEFT, padx=10)
        
        zoom_out_btn = tk.Button(control_frame, text="Zoom Out", command=zoom_out,
                                font=("Arial", 11), bg="#3498db", fg="white",
                                activebackground="#2980b9", activeforeground="white")
        zoom_out_btn.pack(side=tk.LEFT, padx=10)
        
        stats_frame = tk.Frame(control_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(side=tk.LEFT, padx=20)
        
        recent_data = self.econ_data.iloc[-1]
        stats_text = f"""
        Latest GDP (2020): ${recent_data['GDP (current US$)'] / 1e9:.2f} Billion
        Latest GDP per Capita (2020): ${recent_data['GDP per capita (current US$)']:.2f}
        Average GDP Growth (1960-2020): {self.econ_data['GDP growth (annual %)'].mean():.2f}%
        Highest GDP Growth: {self.econ_data['GDP growth (annual %)'].max():.2f}% in {self.econ_data.loc[self.econ_data['GDP growth (annual %)'].idxmax(), 'Year']}
        Lowest GDP Growth: {self.econ_data['GDP growth (annual %)'].min():.2f}% in {self.econ_data.loc[self.econ_data['GDP growth (annual %)'].idxmin(), 'Year']}
        """
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 11), 
                             bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack()
        
        update_gdp_plot()
        
    def show_population_life_expectancy(self):
        """Show population and life expectancy chart"""
        self.clear_chart_frame()
        self.update_header("Population & Life Expectancy Trends")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        ax1.plot(self.econ_data['Year'], self.econ_data['Population, total'] / 1e9, 
                marker='o', linestyle='-', color='#3498db', linewidth=2)
        ax1.set_ylabel('Population (Billions)', fontsize=12, fontweight='bold')
        ax1.set_title('India Population Growth (1960-2020)', fontsize=14, fontweight='bold')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        ax1_twin = ax1.twinx()
        ax1_twin.plot(self.econ_data['Year'], self.econ_data['Population growth (annual %)'], 
                     marker='^', linestyle='--', color='#e74c3c', linewidth=2)
        ax1_twin.set_ylabel('Population Growth Rate (%)', fontsize=12, fontweight='bold', color='#e74c3c')
        ax1_twin.tick_params(axis='y', labelcolor='#e74c3c')
        
        ax1.legend(['Population'], loc='upper left')
        ax1_twin.legend(['Growth Rate'], loc='upper right')
        
        ax2.plot(self.econ_data['Year'], self.econ_data['Life expectancy at birth, total (years)'], 
                marker='s', linestyle='-', color='#2ecc71', linewidth=2)
        ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Life Expectancy (Years)', fontsize=12, fontweight='bold')
        ax2.set_title('Life Expectancy at Birth (1960-2020)', fontsize=14, fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        ax2.set_xticks(self.econ_data['Year'][::5])
        
        plt.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        stats_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(fill=tk.X, pady=10)
        
        first_year = self.econ_data.iloc[0]['Year']
        last_year = self.econ_data.iloc[-1]['Year']
        
        first_pop = self.econ_data.iloc[0]['Population, total'] / 1e6
        last_pop = self.econ_data.iloc[-1]['Population, total'] / 1e6
        
        first_life = self.econ_data.iloc[0]['Life expectancy at birth, total (years)']
        last_life = self.econ_data.iloc[-1]['Life expectancy at birth, total (years)']
        
        stats_text = f"""
        Population in {first_year}: {first_pop:.2f} Million
        Population in {last_year}: {last_pop:.2f} Million
        Population increase: {(last_pop - first_pop):.2f} Million ({((last_pop/first_pop)-1)*100:.2f}% growth)
        
        Life expectancy in {first_year}: {first_life:.1f} years
        Life expectancy in {last_year}: {last_life:.1f} years
        Improvement in life expectancy: {(last_life - first_life):.1f} years ({((last_life/first_life)-1)*100:.2f}% increase)
        
        Current population growth rate (2020): {self.econ_data.iloc[-1]['Population growth (annual %)']:.2f}%
        """
        
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 11), 
                             bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack(padx=20)
        
        self.current_chart = fig
        
    def show_inflation_trends(self):
        """Show inflation trends chart using India_Inflation_Rate.csv"""
        self.clear_chart_frame()
        self.update_header("Inflation Trends (1960-2022)")
    
        # Widget 4: Chart Type Selector
        self.chart_type_var = tk.StringVar(value="Line")
    
        def update_inflation_plot():
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
        
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
            chart_type = self.chart_type_var.get()
            data = self.inflation_data.sort_values('Year')  # Ensure chronological order
        
            # Check if data is empty
            if data.empty:
                messagebox.showerror("Error", "No inflation data available for the specified period.")
                return
        
            # Plot Inflation Rate
            if chart_type == "Line":
                ax1.plot(data['Year'], data['Inflation Rate (%)'], 
                    marker='o', linestyle='-', color='#e74c3c', linewidth=2)
            else:  # Bar
                ax1.bar(data['Year'], data['Inflation Rate (%)'], 
                    color='#e74c3c', alpha=0.7, width=0.6)
        
            ax1.axhline(y=5, color='green', linestyle='--', alpha=0.7, label='Moderate Inflation (5%)')
            ax1.axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='High Inflation (10%)')
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.set_ylabel('Inflation Rate (%)', fontsize=12, fontweight='bold')
            ax1.set_title('India Inflation Trends (1960-2022)', fontsize=14, fontweight='bold')
            ax1.legend(loc='upper right')
        
            
            # Plot Inflation Growth Rate
            if chart_type == "Line":
                ax2.plot(data['Year'], data['Inflation Growth Rate (%)'], 
                    marker='s', linestyle='--', color='#2ecc71', linewidth=2)
            else:  # Bar
                ax2.bar(data['Year'], data['Inflation Growth Rate (%)'], 
                    color='#2ecc71', alpha=0.7, width=0.6)
        
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Inflation Growth Rate (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Annual Change in Inflation Rate (1960-2022)', fontsize=14, fontweight='bold')
        
            ax2.set_xticks(data['Year'][::5])
        
            plt.tight_layout()
            self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.current_chart = fig
    
        stats_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(fill=tk.X, pady=10)
    
        control_frame = tk.Frame(stats_frame, bg=self.light_theme['chart_bg'])
        control_frame.pack(side=tk.LEFT, padx=20)
    
        tk.Label(control_frame, text="Chart Type:", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=5)
        chart_type_dropdown = ttk.Combobox(control_frame, textvariable=self.chart_type_var, 
                                     values=["Line", "Bar"], width=10)
        chart_type_dropdown.pack(side=tk.LEFT, padx=5)
        chart_type_dropdown.bind("<<ComboboxSelected>>", lambda e: update_inflation_plot())
    
        # Handle potential missing or invalid data
        try:
            avg_inflation = self.inflation_data['Inflation Rate (%)'].mean()
            median_inflation = self.inflation_data['Inflation Rate (%)'].median()
            max_inflation = self.inflation_data['Inflation Rate (%)'].max()
            max_inflation_year = self.inflation_data.loc[self.inflation_data['Inflation Rate (%)'].idxmax(), 'Year']
            min_inflation = self.inflation_data['Inflation Rate (%)'].min()
            min_inflation_year = self.inflation_data.loc[self.inflation_data['Inflation Rate (%)'].idxmin(), 'Year']
            recent_inflation = self.inflation_data.iloc[-1]['Inflation Rate (%)']  # Most recent (2022)
        
            avg_growth = self.inflation_data['Inflation Growth Rate (%)'].mean()
            max_growth = self.inflation_data['Inflation Growth Rate (%)'].max()
            max_growth_year = self.inflation_data.loc[self.inflation_data['Inflation Growth Rate (%)'].idxmax(), 'Year']
        
            self.inflation_data = self.inflation_data.copy()  # Avoid SettingWithCopyWarning
            self.inflation_data['Decade'] = (self.inflation_data['Year'] // 10) * 10
            decade_inflation = self.inflation_data.groupby('Decade')['Inflation Rate (%)'].mean().reset_index()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process inflation data: {str(e)}")
            return
    
        decade_table = tk.Frame(stats_frame, bg=self.light_theme['chart_bg'])
        decade_table.pack(side=tk.RIGHT, padx=20)
    
        tk.Label(decade_table, text="Decade-wise Average Inflation", font=("Arial", 12, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=0, column=0, columnspan=2, pady=5)
    
        tk.Label(decade_table, text="Decade", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=0, padx=10, pady=5)
    
        tk.Label(decade_table, text="Avg. Inflation (%)", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=1, padx=10, pady=5)
    
        for i, (_, row) in enumerate(decade_inflation.iterrows()):
            decade_text = f"{int(row['Decade'])}s"
            tk.Label(decade_table, text=decade_text, font=("Arial", 11), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=0, padx=10, pady=2)
            tk.Label(decade_table, text=f"{row['Inflation Rate (%)']:.2f}%", 
               font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=1, padx=10, pady=2)

        stats_container = tk.Frame(stats_frame, bg=self.light_theme['chart_bg'])
        stats_container.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)

        stats_text = f"""
        Average Inflation (1960-2022): {avg_inflation:.2f}%
        Median Inflation: {median_inflation:.2f}%
        Highest Inflation: {max_inflation:.2f}% in {max_inflation_year}
        Lowest Inflation: {min_inflation:.2f}% in {min_inflation_year}
        Most Recent Inflation (2022): {recent_inflation:.2f}%
    
        Average Inflation Growth Rate: {avg_growth:.2f}%
        Highest Inflation Growth: {max_growth:.2f}% in {max_growth_year}
    
        Years with Inflation > 10%: {len(self.inflation_data[self.inflation_data['Inflation Rate (%)'] > 10])}
        Years with Negative Inflation: {len(self.inflation_data[self.inflation_data['Inflation Rate (%)'] < 0])}
        """
    
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 11), 
                         bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack(side=tk.LEFT, padx=10)
    
        update_inflation_plot()
        
    def show_import_export(self):
        """Show import/export analysis chart"""
        self.clear_chart_frame()
        self.update_header("Import/Export Analysis")

        # Main frame to hold both sections
        main_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section 1: Import/Export Trends Plot
        import_export_frame = tk.Frame(main_frame, bg=self.light_theme['chart_bg'])
        import_export_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))  # Add bottom padding

        fig, ax = plt.subplots(figsize=(12, 3))

        ax.plot(self.econ_data['Year'], self.econ_data['Imports of goods and services (% of GDP)'], 
            marker='o', linestyle='-', color='#3498db', linewidth=2, label='Imports (% of GDP)')

        ax.plot(self.econ_data['Year'], self.econ_data['Exports of goods and services (% of GDP)'], 
            marker='s', linestyle='-', color='#2ecc71', linewidth=2, label='Exports (% of GDP)')

        trade_balance = self.econ_data['Exports of goods and services (% of GDP)'] - self.econ_data['Imports of goods and services (% of GDP)']
        ax.plot(self.econ_data['Year'], trade_balance, 
            marker='^', linestyle='--', color='#e74c3c', linewidth=1.5, label='Trade Balance (% of GDP)')

        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        ax.grid(True, linestyle='--', alpha=0.7)

        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('Percentage of GDP', fontsize=12, fontweight='bold')
        ax.set_title('India Import/Export Trends (1960-2020)', fontsize=14, fontweight='bold')

        ax.set_xticks(self.econ_data['Year'][::5])

        ax.legend(loc='upper left')

        events = [
            (1991, "Economic Liberalization"),
            (2000, "Y2K & IT Boom"),
            (2008, "Global Financial Crisis"),
            (2020, "COVID-19 Pandemic")
        ]

        for year, event in events:
            idx = self.econ_data[self.econ_data['Year'] == year].index
            if len(idx) > 0:
                idx = idx[0]
                imports = self.econ_data.loc[idx, 'Imports of goods and services (% of GDP)']
                ax.annotate(event, xy=(year, imports), xytext=(0, 20), 
                        textcoords='offset points', ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))

        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=import_export_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Controls Frame with Tabs
        controls_frame = tk.Frame(main_frame, bg=self.light_theme['chart_bg'])
        controls_frame.pack(fill=tk.X, pady=10)

        tab_control = ttk.Notebook(controls_frame)

        summary_tab = tk.Frame(tab_control, bg=self.light_theme['chart_bg'])
        tab_control.add(summary_tab, text="Summary Statistics")

        reserves_tab = tk.Frame(tab_control, bg=self.light_theme['chart_bg'])
        tab_control.add(reserves_tab, text="Foreign Reserves")

        tab_control.pack(expand=1, fill=tk.BOTH)

        # Summary Statistics
        first_decade = self.econ_data[self.econ_data['Year'] < 1970]
        last_decade = self.econ_data[self.econ_data['Year'] >= 2010]

        first_decade_avg_imports = first_decade['Imports of goods and services (% of GDP)'].mean()
        first_decade_avg_exports = first_decade['Exports of goods and services (% of GDP)'].mean()

        last_decade_avg_imports = last_decade['Imports of goods and services (% of GDP)'].mean()
        last_decade_avg_exports = last_decade['Exports of goods and services (% of GDP)'].mean()

        max_imports = self.econ_data['Imports of goods and services (% of GDP)'].max()
        max_imports_year = self.econ_data.loc[self.econ_data['Imports of goods and services (% of GDP)'].idxmax(), 'Year']

        max_exports = self.econ_data['Exports of goods and services (% of GDP)'].max()
        max_exports_year = self.econ_data.loc[self.econ_data['Exports of goods and services (% of GDP)'].idxmax(), 'Year']

        summary_text = f"""
        1960s Average:
        - Imports: {first_decade_avg_imports:.2f}% of GDP
        - Exports: {first_decade_avg_exports:.2f}% of GDP
        - Trade Balance: {first_decade_avg_exports - first_decade_avg_imports:.2f}% of GDP

        2010s Average:
        - Imports: {last_decade_avg_imports:.2f}% of GDP
        - Exports: {last_decade_avg_exports:.2f}% of GDP
        - Trade Balance: {last_decade_avg_exports - last_decade_avg_imports:.2f}% of GDP

        Peak Import Level: {max_imports:.2f}% of GDP in {max_imports_year}
        Peak Export Level: {max_exports:.2f}% of GDP in {max_exports_year}

        Current (2020):
        - Imports: {self.econ_data.iloc[-1]['Imports of goods and services (% of GDP)']:.2f}% of GDP
        - Exports: {self.econ_data.iloc[-1]['Exports of goods and services (% of GDP)']:.2f}% of GDP
        - Trade Balance: {self.econ_data.iloc[-1]['Exports of goods and services (% of GDP)'] - self.econ_data.iloc[-1]['Imports of goods and services (% of GDP)']:.2f}% of GDP
        """

        summary_label = tk.Label(summary_tab, text=summary_text, font=("Arial", 11), 
                           bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        summary_label.pack(padx=20, pady=10)

        # Section 2: Foreign Reserves Plot and Stats (in Reserves Tab)
        reserves_plot_frame = tk.Frame(reserves_tab, bg=self.light_theme['chart_bg'])
        reserves_plot_frame.pack(fill=tk.BOTH, expand=True)

        reserves_fig, reserves_ax = plt.subplots(figsize=(10, 6))
        reserves_ax.plot(self.econ_data['Year'], self.econ_data['Total reserves (includes gold, current US$)'] / 1e9, 
                    marker='o', linestyle='-', color='#f39c12', linewidth=2)

        reserves_ax.grid(True, linestyle='--', alpha=0.7)
        reserves_ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        reserves_ax.set_ylabel('Foreign Reserves (Billion US$)', fontsize=12, fontweight='bold')
        reserves_ax.set_title('India Foreign Reserves (1960-2020)', fontsize=14, fontweight='bold')
        reserves_ax.set_xticks(self.econ_data['Year'][::5])

        reserves_canvas = FigureCanvasTkAgg(reserves_fig, master=reserves_plot_frame)
        reserves_canvas.draw()
        reserves_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Foreign Reserves Statistics
        reserves_stats_frame = tk.Frame(reserves_tab, bg=self.light_theme['chart_bg'])
        reserves_stats_frame.pack(fill=tk.X, pady=10)

        reserves_stats = f"""
        Current Foreign Reserves (2020): ${self.econ_data.iloc[-1]['Total reserves (includes gold, current US$)'] / 1e9:.2f} Billion
        Increase since 2000: {(self.econ_data.iloc[-1]['Total reserves (includes gold, current US$)'] - self.econ_data[self.econ_data['Year']==2000].iloc[0]['Total reserves (includes gold, current US$)']) / 1e9:.2f} Billion
        Average Annual Growth (2000-2020): {((self.econ_data.iloc[-1]['Total reserves (includes gold, current US$)'] / self.econ_data[self.econ_data['Year']==2000].iloc[0]['Total reserves (includes gold, current US$)']) ** (1/20) - 1) * 100:.2f}%
        """

        reserves_label = tk.Label(reserves_stats_frame, text=reserves_stats, font=("Arial", 11), 
                            bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        reserves_label.pack(padx=20, pady=10)

        self.current_chart = fig
    def show_tax_analysis(self):
        """Show tax revenue analysis chart"""
        self.clear_chart_frame()
        self.update_header("Import Tax Revenue Analysis")
        
        controls_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        controls_frame.pack(fill=tk.X, pady=10)
        
        tab_control = ttk.Notebook(self.chart_frame)
        
        revenue_tab = tk.Frame(tab_control, bg=self.light_theme['chart_bg'])
        tab_control.add(revenue_tab, text="Revenue Trends")
        
        rates_tab = tk.Frame(tab_control, bg=self.light_theme['chart_bg'])
        tab_control.add(rates_tab, text="Collection Rates")
        
        growth_tab = tk.Frame(tab_control, bg=self.light_theme['chart_bg'])
        tab_control.add(growth_tab, text="Growth Analysis")
        
        tab_control.pack(expand=1, fill=tk.BOTH)
        
        revenue_fig, revenue_ax = plt.subplots(figsize=(10, 5))
        revenue_ax.bar(self.tax_data['Year'], self.tax_data['Net Custom Revenue from Import Duties (in ? Crore)'], 
                      color='#3498db')
        
        revenue_ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        revenue_ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        revenue_ax.set_ylabel('Revenue (₹ Crore)', fontsize=12, fontweight='bold')
        revenue_ax.set_title('Net Custom Revenue from Import Duties (2000-2017)', fontsize=14, fontweight='bold')
        
        revenue_ax.set_xticks(self.tax_data['Year'])
        revenue_ax.set_xticklabels([f"{year}" for year in self.tax_data['Year']], rotation=45)
        
        plt.tight_layout()
        
        revenue_canvas = FigureCanvasTkAgg(revenue_fig, master=revenue_tab)
        revenue_canvas.draw()
        revenue_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        rates_fig, rates_ax = plt.subplots(figsize=(10, 5))
        rates_ax.plot(self.tax_data['Year'], self.tax_data['Collection Rates (Percent)'], 
                     marker='o', linestyle='-', color='#e74c3c', linewidth=2)
        
        rates_ax.grid(True, linestyle='--', alpha=0.7)
        rates_ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        rates_ax.set_ylabel('Collection Rate (%)', fontsize=12, fontweight='bold')
        rates_ax.set_title('Import Duties Collection Rates (2000-2017)', fontsize=14, fontweight='bold')
        
        rates_ax.set_xticks(self.tax_data['Year'])
        rates_ax.set_xticklabels([f"{year}" for year in self.tax_data['Year']], rotation=45)
        
        plt.tight_layout()
        
        rates_canvas = FigureCanvasTkAgg(rates_fig, master=rates_tab)
        rates_canvas.draw()
        rates_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        growth_fig, growth_ax = plt.subplots(figsize=(10, 5))
        
        width = 0.35
        indices = range(len(self.tax_data) - 1)
        
        growth_ax.bar([i - width/2 for i in indices], self.tax_data['Growth in Value of Imports ( %)'][1:], 
                      width, color='#3498db', label='Import Value Growth (%)')
        
        growth_ax.bar([i + width/2 for i in indices], self.tax_data['Growth in Revenue from Import Duty (%)'][1:], 
                      width, color='#e74c3c', label='Import Revenue Growth (%)')
        
        growth_ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        growth_ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        growth_ax.set_ylabel('Growth Rate (%)', fontsize=12, fontweight='bold')
        growth_ax.set_title('Comparison of Import Value vs. Revenue Growth (2001-2017)', fontsize=14, fontweight='bold')
        
        growth_ax.set_xticks(indices)
        growth_ax.set_xticklabels([f"{year}" for year in self.tax_data['Year'][1:]], rotation=45)
        
        growth_ax.legend()
        
        plt.tight_layout()
        
        growth_canvas = FigureCanvasTkAgg(growth_fig, master=growth_tab)
        growth_canvas.draw()
        growth_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        stats_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(fill=tk.X, pady=10)
        
        avg_collection_rate = self.tax_data['Collection Rates (Percent)'].mean()
        min_collection_rate = self.tax_data['Collection Rates (Percent)'].min()
        min_year = self.tax_data.loc[self.tax_data['Collection Rates (Percent)'].idxmin(), 'Year']
        max_collection_rate = self.tax_data['Collection Rates (Percent)'].max()
        max_year = self.tax_data.loc[self.tax_data['Collection Rates (Percent)'].idxmax(), 'Year']
        
        total_import_growth = ((self.tax_data.iloc[-1]['Value of Import (in ? Crore)'] / 
                              self.tax_data.iloc[0]['Value of Import (in ? Crore)']) - 1) * 100
        
        total_revenue_growth = ((self.tax_data.iloc[-1]['Net Custom Revenue from Import Duties (in ? Crore)'] / 
                               self.tax_data.iloc[0]['Net Custom Revenue from Import Duties (in ? Crore)']) - 1) * 100
        
        stats_text = f"""
        Average Collection Rate (2000-2017): {avg_collection_rate:.2f}%
        Minimum Collection Rate: {min_collection_rate:.2f}% in {min_year}
        Maximum Collection Rate: {max_collection_rate:.2f}% in {max_year}
        
        Total Import Value Growth (2000-2017): {total_import_growth:.2f}%
        Total Import Revenue Growth (2000-2017): {total_revenue_growth:.2f}%
        
        Current Collection Rate (2017): {self.tax_data.iloc[-1]['Collection Rates (Percent)']:.2f}%
        """
        
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 11), 
                             bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack(padx=20)
        
        self.current_chart = revenue_fig
        
    def show_government_debt(self):
        """Show government debt analysis chart using India_Government_Debt.csv"""
        self.clear_chart_frame()
        self.update_header("Government Debt Analysis (1990-2018)")
    
        # Widget 4: Chart Type Selector
        self.chart_type_var = tk.StringVar(value="Line")
    
        def update_debt_plot():
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
        
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
            chart_type = self.chart_type_var.get()
            # Filter data for 1990-2018 (non-zero debt values)
            data = self.debt_data[(self.debt_data['Year'] >= 1990) & 
                            (self.debt_data['Year'] <= 2018) & 
                            (self.debt_data['Government Debt (% of GDP)'] > 0)].sort_values('Year')
        
            # Check if data is empty
            if data.empty:
                messagebox.showerror("Error", "No government debt data available for the specified period.")
                return
        
            # Plot Government Debt as % of GDP
            if chart_type == "Line":
                ax1.plot(data['Year'], data['Government Debt (% of GDP)'], 
                    marker='o', linestyle='-', color='#f39c12', linewidth=2)
            else:  # Bar
                ax1.bar(data['Year'], data['Government Debt (% of GDP)'], 
                   color='#f39c12', alpha=0.7)
        
            ax1.axhline(y=60, color='red', linestyle='--', alpha=0.7, label='High Debt Threshold (60%)')
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.set_ylabel('Debt (% of GDP)', fontsize=12, fontweight='bold')
            ax1.set_title('India Government Debt as % (1990-2018)', fontsize=14, fontweight='bold')
            ax1.legend(loc='upper right')
        
            # Plot Debt Growth Rate
            if chart_type == "Line":
                ax2.plot(data['Year'], data['Debt Growth Rate (%)'], 
                    marker='s', linestyle='--', color='#9b59b6', linewidth=2)
            else:  # Bar
                ax2.bar(data['Year'], data['Debt Growth Rate (%)'], 
                   color='#9b59b6', alpha=0.7)
        
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Debt Growth Rate (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Annual Change in Government Debt (1990-2018)', fontsize=14, fontweight='bold')
        
            ax2.set_xticks(data['Year'][::2])  # Every 2 years for clarity
        
            plt.tight_layout()
            self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.current_chart = fig
    
        stats_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(fill=tk.X, pady=10)
    
        control_frame = tk.Frame(stats_frame, bg=self.light_theme['chart_bg'])
        control_frame.pack(side=tk.LEFT, padx=20)
    
        tk.Label(control_frame, text="Chart Type:", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=5)
        chart_type_dropdown = ttk.Combobox(control_frame, textvariable=self.chart_type_var, 
                                     values=["Line", "Bar"], width=10)
        chart_type_dropdown.pack(side=tk.LEFT, padx=5)
        chart_type_dropdown.bind("<<ComboboxSelected>>", lambda e: update_debt_plot())
    
        # Handle potential missing or invalid data
        try:
            filtered_data = self.debt_data[(self.debt_data['Year'] >= 1990) & 
                                     (self.debt_data['Year'] <= 2018) & 
                                     (self.debt_data['Government Debt (% of GDP)'] > 0)]
        
            if filtered_data.empty:
                messagebox.showerror("Error", "No valid government debt data available for 1990-2018.")
                return
        
            avg_debt = filtered_data['Government Debt (% of GDP)'].mean()
            max_debt = filtered_data['Government Debt (% of GDP)'].max()
            max_debt_year = filtered_data.loc[filtered_data['Government Debt (% of GDP)'].idxmax(), 'Year']
            min_debt = filtered_data['Government Debt (% of GDP)'].min()
            min_debt_year = filtered_data.loc[filtered_data['Government Debt (% of GDP)'].idxmin(), 'Year']
            recent_debt = filtered_data.iloc[-1]['Government Debt (% of GDP)']  # Most recent (2018)
        
            avg_growth = filtered_data['Debt Growth Rate (%)'].mean()
            max_growth = filtered_data['Debt Growth Rate (%)'].max()
            max_growth_year = filtered_data.loc[filtered_data['Debt Growth Rate (%)'].idxmax(), 'Year']
        
            filtered_data = filtered_data.copy()  # Avoid SettingWithCopyWarning
            filtered_data['Decade'] = (filtered_data['Year'] // 10) * 10
            decade_debt = filtered_data.groupby('Decade')['Government Debt (% of GDP)'].mean().reset_index()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process government debt data: {str(e)}")
            return
    
        decade_table = tk.Frame(stats_frame, bg=self.light_theme['chart_bg'])
        decade_table.pack(side=tk.RIGHT, padx=20)
    
        tk.Label(decade_table, text="Decade-wise Average Debt", font=("Arial", 12, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=0, column=0, columnspan=2, pady=5)
    
        tk.Label(decade_table, text="Decade", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=0, padx=10, pady=5)
    
        tk.Label(decade_table, text="Avg. Debt (% of GDP)", font=("Arial", 11, "bold"), 
           bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=1, padx=10, pady=5)
    
        for i, (_, row) in enumerate(decade_debt.iterrows()):
            decade_text = f"{int(row['Decade'])}s"
            tk.Label(decade_table, text=decade_text, font=("Arial", 11), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=0, padx=10, pady=2)
            tk.Label(decade_table, text=f"{row['Government Debt (% of GDP)']:.2f}%", 
               font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=1, padx=10, pady=2)
    
        stats_text = f"""
        Average Debt (1990-2018): {avg_debt:.2f}% of GDP
        Highest Debt: {max_debt:.2f}% in {max_debt_year}
        Lowest Debt: {min_debt:.2f}% in {min_debt_year}
        Most Recent Debt (2018): {recent_debt:.2f}%
    
        Average Debt Growth Rate: {avg_growth:.2f}%
        Highest Debt Growth: {max_growth:.2f}% in {max_growth_year}
    
        Years with Debt > 60%: {len(filtered_data[filtered_data['Government Debt (% of GDP)'] > 60])}
        """
    
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Arial", 11), 
                         bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack(side=tk.LEFT, padx=20)
    
        update_debt_plot()
        
    def show_growth_indicators(self):
        """Show economic growth indicators chart"""
        self.clear_chart_frame()
        self.update_header("Economic Growth Indicators")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        ax1.plot(self.econ_data['Year'], self.econ_data['GDP growth (annual %)'], 
                marker='o', linestyle='-', color='#3498db', linewidth=2)
        
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        ax1.set_ylabel('GDP Growth Rate (%)', fontsize=12, fontweight='bold')
        ax1.set_title('GDP Annual Growth Rate (1960-2020)', fontsize=14, fontweight='bold')
        
        events = [
            (1979, "Oil Crisis"),
            (1991, "Economic Liberalization"),
            (2008, "Global Financial Crisis"),
            (2016, "Demonetization"),
            (2020, "COVID-19 Pandemic")
        ]
        
        for year, event in events:
            idx = self.econ_data[self.econ_data['Year'] == year].index
            if len(idx) > 0:
                idx = idx[0]
                growth = self.econ_data.loc[idx, 'GDP growth (annual %)']
                ax1.annotate(event, xy=(year, growth), xytext=(0, 15 if growth > 0 else -15), 
                           textcoords='offset points', ha='center', va='bottom' if growth > 0 else 'top',
                           bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))
        
        ax2.plot(self.inflation_data['Year'], self.inflation_data['Inflation Rate (%)'], 
                marker='s', linestyle='-', color='#e74c3c', linewidth=2)
        
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Inflation Rate (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Inflation Rate (1960-2022)', fontsize=14, fontweight='bold')
        
        ax2.set_xticks(self.inflation_data['Year'][::5])
        
        plt.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        controls_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        controls_frame.pack(fill=tk.X, pady=10)
        
        self.inflation_data = self.inflation_data.copy()  # Avoid SettingWithCopyWarning
        self.inflation_data['Decade'] = (self.inflation_data['Year'] // 10) * 10
        decade_stats = self.inflation_data.groupby('Decade').agg({
            'Inflation Rate (%)': 'mean'
        }).reset_index()
        decade_stats['GDP Growth (annual %)'] = self.econ_data.groupby((self.econ_data['Year'] // 10) * 10)['GDP growth (annual %)'].mean().reindex(decade_stats['Decade']).values
        
        stats_frame = tk.Frame(controls_frame, bg=self.light_theme['chart_bg'])
        stats_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(stats_frame, text="Decade-wise Growth & Inflation", font=("Arial", 12, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=0, column=0, columnspan=3, pady=5)
        
        tk.Label(stats_frame, text="Decade", font=("Arial", 11, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=0, padx=10, pady=5)
        
        tk.Label(stats_frame, text="Avg. GDP Growth (%)", font=("Arial", 11, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(stats_frame, text="Avg. Inflation (%)", font=("Arial", 11, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=1, column=2, padx=10, pady=5)
        
        for i, (_, row) in enumerate(decade_stats.iterrow()):
            decade_text = f"{int(row['Decade'])}s"
            tk.Label(stats_frame, text=decade_text, font=("Arial", 11), 
                   bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=0, padx=10, pady=2)
            tk.Label(stats_frame, text=f"{row['GDP Growth (annual %)']:.2f}%", 
                   font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=1, padx=10, pady=2)
            tk.Label(stats_frame, text=f"{row['Inflation Rate (%)']:.2f}%", 
                   font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e").grid(row=i+2, column=2, padx=10, pady=2)
        
        stats_text = f"""
        GDP Growth Stats (1960-2020):
        - Average GDP Growth: {self.econ_data['GDP growth (annual %)'].mean():.2f}%
        - Highest GDP Growth: {self.econ_data['GDP growth (annual %)'].max():.2f}% in {self.econ_data.loc[self.econ_data['GDP growth (annual %)'].idxmax(), 'Year']}
        - Lowest GDP Growth: {self.econ_data['GDP growth (annual %)'].min():.2f}% in {self.econ_data.loc[self.econ_data['GDP growth (annual %)'].idxmin(), 'Year']}
        
        Inflation Stats (1960-2022):
        - Average Inflation: {self.inflation_data['Inflation Rate (%)'].mean():.2f}%
        - Highest Inflation: {self.inflation_data['Inflation Rate (%)'].max():.2f}% in {self.inflation_data.loc[self.inflation_data['Inflation Rate (%)'].idxmax(), 'Year']}
        - Lowest Inflation: {self.inflation_data['Inflation Rate (%)'].min():.2f}% in {self.inflation_data.loc[self.inflation_data['Inflation Rate (%)'].idxmin(), 'Year']}
        """
        
        stats_label = tk.Label(controls_frame, text=stats_text, font=("Arial", 11), 
                             bg=self.light_theme['chart_bg'], fg="#34495e", justify=tk.LEFT)
        stats_label.pack(side=tk.LEFT, padx=20)
        
        self.current_chart = fig
        
    def show_compare_indicators(self):
        """Show comparison plot for selected indicators"""
        self.clear_chart_frame()
        self.update_header("Compare Economic Indicators")
        
        indicators = [
            'GDP (current US$)', 'GDP per capita (current US$)', 'GDP growth (annual %)',
            'Population, total', 'Population growth (annual %)', 
            'Life expectancy at birth, total (years)', 
            'Imports of goods and services (% of GDP)', 
            'Exports of goods and services (% of GDP)', 
            'Total reserves (includes gold, current US$)',
            'Inflation Rate (%)', 'Inflation Growth Rate (%)',
            'Government Debt (% of GDP)', 'Debt Growth Rate (%)'
        ]
        
        self.selected_indicators = []
        self.check_vars = {ind: tk.BooleanVar(value=False) for ind in indicators}
        
        # Widget 2: Year Range Slider
        min_year = min(self.econ_data['Year'].min(), self.inflation_data['Year'].min(), self.debt_data['Year'].min())
        max_year = max(self.econ_data['Year'].max(), self.inflation_data['Year'].max(), self.debt_data['Year'].max())
        
        self.start_year_var = tk.DoubleVar(value=min_year)
        self.end_year_var = tk.DoubleVar(value=max_year)
        
        def update_year_labels():
            start_label.config(text=f"Start Year: {int(self.start_year_var.get())}")
            end_label.config(text=f"End Year: {int(self.end_year_var.get())}")
        
        def generate_plot():
            self.selected_indicators = [ind for ind, var in self.check_vars.items() if var.get()]
            
            if len(self.selected_indicators) < 1 or len(self.selected_indicators) > 3:
                messagebox.showwarning("Warning", "Please select 1 to 3 indicators to compare.")
                return
                
            start_year = int(self.start_year_var.get())
            end_year = int(self.end_year_var.get())
            
            if start_year >= end_year:
                messagebox.showwarning("Warning", "Start year must be less than end year.")
                return
                
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            colors = ['#3498db', '#e74c3c', '#2ecc71']
            for i, indicator in enumerate(self.selected_indicators):
                if indicator in self.econ_data.columns:
                    data = self.econ_data[(self.econ_data['Year'] >= start_year) & (self.econ_data['Year'] <= end_year)]
                    y_data = data[indicator]
                    if indicator == 'GDP (current US$)':
                        y_data = y_data / 1e9
                        ylabel = 'GDP (Billion US$)'
                    elif indicator == 'Population, total':
                        y_data = y_data / 1e6
                        ylabel = 'Population (Million)'
                    elif indicator == 'Total reserves (includes gold, current US$)':
                        y_data = y_data / 1e9
                        ylabel = 'Reserves (Billion US$)'
                    else:
                        ylabel = indicator
                elif indicator in self.inflation_data.columns:
                    data = self.inflation_data[(self.inflation_data['Year'] >= start_year) & (self.inflation_data['Year'] <= end_year)]
                    y_data = data[indicator]
                    ylabel = indicator
                elif indicator in self.debt_data.columns:
                    data = self.debt_data[(self.debt_data['Year'] >= start_year) & (self.debt_data['Year'] <= end_year)]
                    y_data = data[indicator]
                    ylabel = indicator
                else:
                    continue
                
                ax.plot(data['Year'], y_data, marker='o', linestyle='-', color=colors[i % len(colors)], 
                       linewidth=2, label=indicator)
            
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_xlabel('Year', fontsize=12, fontweight='bold')
            ax.set_ylabel('Value', fontsize=12, fontweight='bold')
            ax.set_title(f'Comparison of Selected Indicators ({start_year}-{end_year})', fontsize=14, fontweight='bold')
            ax.legend(loc='upper left')
            ax.set_xticks(data['Year'][::2])
            
            plt.tight_layout()
            self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.current_chart = fig
            
            # Correlation Analysis
            correlation_text = "Correlation Coefficients:\n"
            for i, ind1 in enumerate(self.selected_indicators):
                for j, ind2 in enumerate(self.selected_indicators[i+1:], i+1):
                    if ind1 in self.econ_data.columns:
                        data1 = self.econ_data[(self.econ_data['Year'] >= start_year) & (self.econ_data['Year'] <= end_year)][ind1]
                    elif ind1 in self.inflation_data.columns:
                        data1 = self.inflation_data[(self.inflation_data['Year'] >= start_year) & (self.inflation_data['Year'] <= end_year)][ind1]
                    else:
                        data1 = self.debt_data[(self.debt_data['Year'] >= start_year) & (self.debt_data['Year'] <= end_year)][ind1]
                        
                    if ind2 in self.econ_data.columns:
                        data2 = self.econ_data[(self.econ_data['Year'] >= start_year) & (self.econ_data['Year'] <= end_year)][ind2]
                    elif ind2 in self.inflation_data.columns:
                        data2 = self.inflation_data[(self.inflation_data['Year'] >= start_year) & (self.inflation_data['Year'] <= end_year)][ind2]
                    else:
                        data2 = self.debt_data[(self.debt_data['Year'] >= start_year) & (self.debt_data['Year'] <= end_year)][ind2]
                    
                    # Align data by year
                    df_temp = pd.DataFrame({'ind1': data1, 'ind2': data2, 'Year': data['Year']})
                    df_temp = df_temp.dropna()
                    if not df_temp.empty:
                        correlation = df_temp['ind1'].corr(df_temp['ind2'])
                        correlation_text += f"{ind1} vs {ind2}: {correlation:.2f}\n"
            
            correlation_label.config(text=correlation_text)
        
        control_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        control_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(control_frame, text="Select Year Range:", font=("Arial", 11, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=10)
        
        start_label = tk.Label(control_frame, text=f"Start Year: {int(self.start_year_var.get())}", 
                             font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e")
        start_label.pack(side=tk.LEFT, padx=5)
        
        start_slider = ttk.Scale(control_frame, from_=min_year, to=max_year, 
                                orient=tk.HORIZONTAL, variable=self.start_year_var, 
                                command=lambda x: update_year_labels())
        start_slider.pack(side=tk.LEFT, padx=10)
        
        end_label = tk.Label(control_frame, text=f"End Year: {int(self.end_year_var.get())}", 
                           font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e")
        end_label.pack(side=tk.LEFT, padx=5)
        
        end_slider = ttk.Scale(control_frame, from_=min_year, to=max_year, 
                              orient=tk.HORIZONTAL, variable=self.end_year_var, 
                              command=lambda x: update_year_labels())
        end_slider.pack(side=tk.LEFT, padx=10)
        
        # Widget 3: Indicator Checkbox List
        indicators_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        indicators_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(indicators_frame, bg=self.light_theme['chart_bg'])
        scrollbar = ttk.Scrollbar(indicators_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.light_theme['chart_bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(scrollable_frame, text="Select Indicators (up to 3):", font=("Arial", 12, "bold"), 
               bg=self.light_theme['chart_bg'], fg="#34495e").pack(anchor='w', padx=10, pady=5)
        
        for indicator in indicators:
            chk = tk.Checkbutton(scrollable_frame, text=indicator, variable=self.check_vars[indicator], 
                               font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e", 
                               selectcolor="#d9d9d9", activebackground=self.light_theme['chart_bg'])
            chk.pack(anchor='w', padx=20, pady=2)
        
        generate_btn = tk.Button(self.chart_frame, text="Generate Comparison Plot", 
                               command=generate_plot, font=("Arial", 11), bg="#3498db", fg="white",
                               activebackground="#2980b9", activeforeground="white")
        generate_btn.pack(pady=10)
        
        correlation_label = tk.Label(self.chart_frame, text="Correlation Coefficients:\nSelect indicators to see correlations", 
                                  font=("Arial", 11), bg=self.light_theme['chart_bg'], fg="#34495e", 
                                  justify=tk.LEFT)
        correlation_label.pack(padx=20, pady=10)
        
    def show_data_table(self):
        """Show data table view"""
        self.clear_chart_frame()
        self.update_header("Data Table View")
        
        datasets = {
            "Indian Economy Data": self.econ_data,
            "Import Tax Data": self.tax_data,
            "Inflation Data": self.inflation_data,
            "Government Debt Data": self.debt_data
        }
        
        self.dataset_var = tk.StringVar(value="Indian Economy Data")
        self.filter_var = tk.StringVar(value="All Columns")
        self.search_var = tk.StringVar()
        
        def update_table():
            for item in tree.get_children():
                tree.delete(item)
            
            selected_dataset = self.dataset_var.get()
            df = datasets[selected_dataset].copy()
            
            search_text = self.search_var.get().lower()
            filter_column = self.filter_var.get()
            
            if search_text:
                if filter_column == "All Columns":
                    mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(search_text).any(), axis=1)
                else:
                    mask = df[filter_column].astype(str).str.lower().str.contains(search_text)
                df = df[mask]
            
            for _, row in df.iterrows():
                tree.insert("", tk.END, values=[row[col] for col in df.columns])
        
        def update_columns():
            selected_dataset = self.dataset_var.get()
            columns = ["All Columns"] + list(datasets[selected_dataset].columns)
            filter_dropdown['values'] = columns
            self.filter_var.set("All Columns")
            tree.delete(*tree.get_children())
            tree['columns'] = datasets[selected_dataset].columns
            for col in tree['columns']:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor='w')
            update_table()
        
        control_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        control_frame.pack(fill=tk.X, pady=10)
        
        # Dataset selection
        tk.Label(control_frame, text="Select Dataset:", font=("Arial", 11, "bold"), 
                bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=10)
        
        dataset_dropdown = ttk.Combobox(control_frame, textvariable=self.dataset_var, 
                                      values=list(datasets.keys()), width=20)
        dataset_dropdown.pack(side=tk.LEFT, padx=5)
        dataset_dropdown.bind("<<ComboboxSelected>>", lambda e: update_columns())
        
        # Column filter
        tk.Label(control_frame, text="Filter Column:", font=("Arial", 11, "bold"), 
                bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=10)
        
        filter_dropdown = ttk.Combobox(control_frame, textvariable=self.filter_var, 
                                     values=["All Columns"], width=20)
        filter_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Search
        tk.Label(control_frame, text="Search:", font=("Arial", 11, "bold"), 
                bg=self.light_theme['chart_bg'], fg="#34495e").pack(side=tk.LEFT, padx=10)
        
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: update_table())
        
        # Treeview
        tree_frame = tk.Frame(self.chart_frame, bg=self.light_theme['chart_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, 
                          xscrollcommand=tree_scroll_x.set, height=20)
        tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)
        
        # Initial table setup
        update_columns()
        
        # Export data button
        def export_data():
            selected_dataset = self.dataset_var.get()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    datasets[selected_dataset].to_csv(file_path, index=False)
                    messagebox.showinfo("Success", f"Data exported successfully to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export data: {str(e)}")
        
        export_btn = tk.Button(control_frame, text="Export Table", 
                             command=export_data, font=("Arial", 11), 
                             bg="#3498db", fg="white",
                             activebackground="#2980b9", activeforeground="white")
        export_btn.pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = IndianEconomyDashboard(root)
    root.mainloop()