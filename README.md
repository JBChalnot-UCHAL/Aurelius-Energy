# Financial Simulator

This is a Streamlit-based web application that provides a comprehensive financial simulation of a manufacturing company. It is designed to help users understand the impact of strategic business decisions on financial outcomes over a five-year period (from year X7 to X11).

## Features

- **Dynamic Simulation:** The application runs a year-by-year simulation, where the outcomes of one year serve as the inputs for the next.
- **Interactive Decision-Making:** Users can adjust a wide range of strategic parameters for each year, including:
  - **Pricing:** Set the unit selling price.
  - **Production:** Define target production volume. The simulator automatically handles the acquisition of new production lines and the hiring of personnel to meet these targets.
  - **Sales:** Specify target sales volume.
  - **Marketing:** Allocate a fixed budget for marketing activities.
  - **Dividends:** Decide on the amount of dividends to be paid out from the previous year's profits.
  - **Financing:** In year X8, users have the option to refinance the company's long-term debt by specifying the new loan amount, interest rate, and duration.
- **Comprehensive Financial Reporting:** For each year of the simulation, the application generates detailed financial statements in an Excel-style layout, including:
  - **Cash Flow Statement:** Tracks the flow of cash from operating, investing, and financing activities.
  - **Income Statement:** Reports on the company's revenues, expenses, and profitability.
  - **Balance Sheet:** Provides a snapshot of the company's assets, liabilities, and equity.
- **Key Performance Indicators (KPIs):** The dashboard highlights critical financial metrics such as Net Income, Ending Cash Balance, Return on Equity (ROE), and the Current Ratio to help users quickly assess the company's financial health.
- **Detailed Operational Tracking:** The application also provides insights into:
  - **Capacity and Asset Lifecycle:** Monitors the age and capacity of production lines, including purchases of new lines and scrapping of old ones.
  - **Inventory Flow:** Tracks the movement of finished goods and raw materials, showing opening and ending stock levels, production, sales, and purchases.
- **Scenario Analysis:** By changing the decision parameters in the sidebar, users can instantly see the effects on the company's financials, allowing for robust scenario and sensitivity analysis.

## Business Logic and Assumptions

The simulation is built on a set of core business and accounting principles:

- **Costs:** The model includes various costs, such as material costs, labor costs, rent, property taxes, and administrative salaries. Some of these, like rent and sales commission rates, change from year X8 onwards to reflect new business conditions.
- **Depreciation:** Production lines are depreciated over their useful life.
- **Debt and Interest:** The company has existing long-term debt with a fixed interest rate. The model also calculates interest on any bank overdrafts that may occur.
- **Taxes:** Corporate income tax is calculated based on the earnings before tax (EBT).
- **Cash Flow:** The simulation models the timing of cash receipts and payments, distinguishing between cash and credit sales/purchases.

## How to Run the Application

To run this financial simulator on your local machine, follow these steps:

1. **Prerequisites:**
   - Make sure you have Python 3.6 or higher installed.
   - You will also need `pip` to install the required Python packages.

2. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

3. **Install Dependencies:**
   The application relies on the Streamlit library. Install it using pip:
   ```bash
   pip install streamlit
   ```

4. **Run the Streamlit App:**
   Once the dependencies are installed, you can run the application using the following command in your terminal:
   ```bash
   streamlit run simu.py
   ```

5. **Access the Application:**
   After running the command, Streamlit will start a local web server. You can access the financial simulator by opening the URL provided in the terminal (usually `http://localhost:8501`) in your web browser.

## Using the Simulator

- The **sidebar on the left** contains all the decision parameters for each year of the simulation (X7 to X11).
- Use the expanders to view and modify the decisions for each year.
- The main panel of the application will display the financial statements and other reports in tabs for each year.
- The simulation updates automatically whenever you change a decision parameter.
- The first tab, "X6," shows the initial financial state of the company at the beginning of the simulation.
