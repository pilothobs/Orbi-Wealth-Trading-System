"""
Risk Management Module for Orbi Wealth Trading System.

This module provides classes and functions for managing risk,
including position sizing, stop-loss, and take-profit calculations.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default risk parameters from environment variables
def parse_env_float(env_var, default):
    """Parse environment variable to float, handling any comments in the value."""
    value = os.getenv(env_var, default)
    # Split by '#' and take only the first part, then strip whitespace
    value = value.split('#')[0].strip()
    return float(value)

DEFAULT_MAX_POSITION_SIZE = parse_env_float('MAX_POSITION_SIZE', '0.02')
DEFAULT_MAX_DRAWDOWN = parse_env_float('MAX_DRAWDOWN', '0.15')
DEFAULT_STOP_LOSS_PERCENTAGE = parse_env_float('STOP_LOSS_PERCENTAGE', '0.02')


class RiskManager:
    """
    Risk Manager for the trading system.
    
    This class handles risk management tasks such as position sizing,
    stop-loss and take-profit calculations, and portfolio risk assessment.
    """
    
    def __init__(self, 
                 max_position_size: float = DEFAULT_MAX_POSITION_SIZE,
                 max_drawdown: float = DEFAULT_MAX_DRAWDOWN,
                 stop_loss_percentage: float = DEFAULT_STOP_LOSS_PERCENTAGE):
        """
        Initialize the risk manager.
        
        Args:
            max_position_size: Maximum position size as a percentage of portfolio value
            max_drawdown: Maximum acceptable drawdown as a percentage
            stop_loss_percentage: Default stop-loss percentage
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.stop_loss_percentage = stop_loss_percentage
        
        logger.info(f"Risk Manager initialized with max_position_size={max_position_size}, "
                   f"max_drawdown={max_drawdown}, stop_loss_percentage={stop_loss_percentage}")
    
    def calculate_position_size(self, 
                               portfolio_value: float, 
                               risk_per_trade: Optional[float] = None,
                               entry_price: Optional[float] = None,
                               stop_loss_price: Optional[float] = None) -> float:
        """
        Calculate the appropriate position size for a trade.
        
        Args:
            portfolio_value: Total portfolio value
            risk_per_trade: Risk per trade as a percentage of portfolio (optional)
            entry_price: Entry price for the trade (optional)
            stop_loss_price: Stop-loss price for the trade (optional)
            
        Returns:
            Position size in units of the base currency
        """
        # If risk_per_trade is not provided, use the default max_position_size
        if risk_per_trade is None:
            risk_per_trade = self.max_position_size
        
        # Calculate the maximum amount to risk
        max_risk_amount = portfolio_value * risk_per_trade
        
        # If entry and stop-loss prices are provided, calculate position size based on risk
        if entry_price is not None and stop_loss_price is not None:
            # Calculate the risk per unit
            risk_per_unit = abs(entry_price - stop_loss_price)
            
            # Avoid division by zero
            if risk_per_unit == 0:
                logger.warning("Risk per unit is zero, using default position size")
                return portfolio_value * self.max_position_size / entry_price
            
            # Calculate position size based on risk
            position_size = max_risk_amount / risk_per_unit
            
            # Convert to units based on entry price
            position_units = position_size / entry_price
            
            logger.info(f"Calculated position size: {position_units} units "
                       f"(value: {position_units * entry_price})")
            
            return position_units
        else:
            # If no entry/stop-loss prices, use a simple percentage of portfolio
            position_value = portfolio_value * self.max_position_size
            
            if entry_price is not None:
                position_units = position_value / entry_price
                logger.info(f"Calculated position size: {position_units} units "
                           f"(value: {position_value})")
                return position_units
            else:
                logger.info(f"Calculated position value: {position_value}")
                return position_value
    
    def calculate_stop_loss(self, 
                           entry_price: float, 
                           direction: str = 'long',
                           atr: Optional[float] = None,
                           atr_multiplier: float = 2.0,
                           custom_percentage: Optional[float] = None) -> float:
        """
        Calculate the stop-loss price for a trade.
        
        Args:
            entry_price: Entry price for the trade
            direction: Trade direction ('long' or 'short')
            atr: Average True Range value (optional)
            atr_multiplier: Multiplier for ATR-based stop-loss
            custom_percentage: Custom stop-loss percentage (optional)
            
        Returns:
            Stop-loss price
        """
        # Determine the stop-loss percentage
        if custom_percentage is not None:
            stop_percentage = custom_percentage
        else:
            stop_percentage = self.stop_loss_percentage
        
        # Calculate stop-loss based on ATR if provided
        if atr is not None:
            stop_distance = atr * atr_multiplier
            
            if direction.lower() == 'long':
                stop_loss = entry_price - stop_distance
            else:  # short
                stop_loss = entry_price + stop_distance
                
            logger.info(f"Calculated ATR-based stop-loss: {stop_loss} "
                       f"(ATR: {atr}, multiplier: {atr_multiplier})")
        else:
            # Calculate stop-loss based on percentage
            if direction.lower() == 'long':
                stop_loss = entry_price * (1 - stop_percentage)
            else:  # short
                stop_loss = entry_price * (1 + stop_percentage)
                
            logger.info(f"Calculated percentage-based stop-loss: {stop_loss} "
                       f"(percentage: {stop_percentage})")
        
        return stop_loss
    
    def calculate_take_profit(self, 
                             entry_price: float, 
                             stop_loss_price: float,
                             direction: str = 'long',
                             risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate the take-profit price for a trade.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss_price: Stop-loss price for the trade
            direction: Trade direction ('long' or 'short')
            risk_reward_ratio: Desired risk-reward ratio
            
        Returns:
            Take-profit price
        """
        # Calculate the risk (distance to stop-loss)
        risk = abs(entry_price - stop_loss_price)
        
        # Calculate the reward (distance to take-profit) based on risk-reward ratio
        reward = risk * risk_reward_ratio
        
        # Calculate take-profit price
        if direction.lower() == 'long':
            take_profit = entry_price + reward
        else:  # short
            take_profit = entry_price - reward
        
        logger.info(f"Calculated take-profit: {take_profit} "
                   f"(risk: {risk}, reward: {reward}, ratio: {risk_reward_ratio})")
        
        return take_profit
    
    def calculate_risk_metrics(self, 
                              portfolio_history: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate risk metrics for a portfolio.
        
        Args:
            portfolio_history: DataFrame with portfolio value history
            
        Returns:
            Dictionary of risk metrics
        """
        if portfolio_history.empty:
            logger.warning("Cannot calculate risk metrics for empty portfolio history")
            return {}
        
        try:
            # Calculate daily returns
            if 'returns' not in portfolio_history.columns:
                portfolio_history['returns'] = portfolio_history['value'].pct_change()
            
            # Calculate key metrics
            metrics = {}
            
            # Volatility (annualized)
            metrics['volatility'] = portfolio_history['returns'].std() * np.sqrt(252)
            
            # Maximum drawdown
            portfolio_history['cumulative_returns'] = (1 + portfolio_history['returns']).cumprod()
            portfolio_history['cumulative_max'] = portfolio_history['cumulative_returns'].cummax()
            portfolio_history['drawdown'] = (portfolio_history['cumulative_returns'] / 
                                           portfolio_history['cumulative_max'] - 1)
            metrics['max_drawdown'] = portfolio_history['drawdown'].min()
            
            # Sharpe ratio (assuming risk-free rate of 0 for simplicity)
            metrics['sharpe_ratio'] = (portfolio_history['returns'].mean() / 
                                     portfolio_history['returns'].std() * np.sqrt(252))
            
            # Sortino ratio (downside deviation)
            negative_returns = portfolio_history['returns'][portfolio_history['returns'] < 0]
            if len(negative_returns) > 0:
                downside_deviation = negative_returns.std() * np.sqrt(252)
                metrics['sortino_ratio'] = (portfolio_history['returns'].mean() / 
                                          downside_deviation * np.sqrt(252))
            else:
                metrics['sortino_ratio'] = float('inf')  # No negative returns
            
            # Calmar ratio
            if metrics['max_drawdown'] != 0:
                metrics['calmar_ratio'] = (portfolio_history['returns'].mean() * 252 / 
                                         abs(metrics['max_drawdown']))
            else:
                metrics['calmar_ratio'] = float('inf')  # No drawdown
            
            logger.info(f"Calculated risk metrics: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}
    
    def check_portfolio_risk(self, 
                            portfolio_history: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the portfolio risk is within acceptable limits.
        
        Args:
            portfolio_history: DataFrame with portfolio value history
            
        Returns:
            Tuple of (is_acceptable, risk_metrics)
        """
        # Calculate risk metrics
        metrics = self.calculate_risk_metrics(portfolio_history)
        
        if not metrics:
            logger.warning("No risk metrics available to check portfolio risk")
            return False, {}
        
        # Check if drawdown exceeds maximum allowed
        is_acceptable = True
        warnings = []
        
        if 'max_drawdown' in metrics and abs(metrics['max_drawdown']) > self.max_drawdown:
            is_acceptable = False
            warnings.append(f"Maximum drawdown ({abs(metrics['max_drawdown']):.2%}) "
                           f"exceeds limit ({self.max_drawdown:.2%})")
        
        # Add other risk checks as needed
        
        result = {
            'is_acceptable': is_acceptable,
            'metrics': metrics,
            'warnings': warnings
        }
        
        logger.info(f"Portfolio risk check: {result}")
        
        return is_acceptable, result


# Example usage
if __name__ == "__main__":
    # Create a risk manager
    rm = RiskManager()
    
    # Calculate position size
    portfolio_value = 100000
    entry_price = 150
    stop_loss_price = 145
    
    position_size = rm.calculate_position_size(
        portfolio_value=portfolio_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price
    )
    
    print(f"Position size: {position_size} units (${position_size * entry_price})")
    
    # Calculate stop-loss and take-profit
    atr = 2.5
    stop_loss = rm.calculate_stop_loss(
        entry_price=entry_price,
        direction='long',
        atr=atr
    )
    
    take_profit = rm.calculate_take_profit(
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        direction='long',
        risk_reward_ratio=2.5
    )
    
    print(f"Entry: ${entry_price}, Stop-Loss: ${stop_loss}, Take-Profit: ${take_profit}")
    
    # Create a sample portfolio history
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    values = [100000]
    
    for _ in range(1, len(dates)):
        daily_return = np.random.normal(0.0005, 0.01)  # Mean 5bps, std 1%
        values.append(values[-1] * (1 + daily_return))
    
    portfolio_history = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Calculate risk metrics
    metrics = rm.calculate_risk_metrics(portfolio_history)
    print("Risk Metrics:", metrics)
    
    # Check portfolio risk
    is_acceptable, risk_result = rm.check_portfolio_risk(portfolio_history)
    print(f"Portfolio risk acceptable: {is_acceptable}")
    if not is_acceptable:
        print(f"Warnings: {risk_result['warnings']}") 