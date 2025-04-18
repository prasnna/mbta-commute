# MBTA Commute Tools

A collection of Python scripts for monitoring and optimizing commutes using MBTA transit services.

## Overview

This project contains tools to help manage commutes on the MBTA system, including:

- Red Line train arrival predictions
- Bus 226 arrival predictions
- Commute bridge for coordinating train-to-bus connections
- Real-time alerts and notifications for optimal departure times

## Features

- **Real-time Predictions**: Get up-to-the-minute arrival predictions for trains and buses
- **Commute Bridge**: Coordinate connections between Red Line trains and 226 buses
- **Smart Notifications**: Receive alerts when it's time to leave for your commute
- **Customizable Settings**: Adjust parameters for your specific commute needs

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MBTA API key (get one from [MBTA Developer Portal](https://api-v3.mbta.com/))
- Required Python packages (see `requirements.txt`)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mbta-commute.git
   cd mbta-commute
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   ```
   cp .env.sample .env
   # Edit .env with your MBTA API key
   ```

### Usage

#### Using Batch Scripts (Recommended)

The easiest way to use this tool is with the provided batch scripts:

```
start_all.bat
```

This will start all three services in separate windows.

#### Monitor Red Line Arrivals

```
python src/red_line.py
```

Or use the batch script:

```
src/Red_Line_Script.bat
```

This will monitor Red Line train arrivals and notify you when it's time to leave.

#### Monitor Bus 226 Arrivals

```
python src/bus_226.py
```

Or use the batch script:

```
src/226_Bus_Script.bat
```

This will monitor Bus 226 arrivals and notify you when it's time to leave.

#### Use the Commute Bridge

```
python src/commute_bridge.py
```

Or use the batch script:

```
src/Commute_Bridge_Script.bat
```

This will coordinate between Red Line trains and Bus 226 to find optimal connections.

## Configuration

The application uses environment variables for configuration:

- `MBTA_API_KEY`: Your MBTA API key

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- The MBTA API key should be kept private

## License

This project is licensed under the MIT License - see the LICENSE file for details.
