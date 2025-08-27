import React from 'react';
import './TransactionsCard.css';

const TransactionsCard = ({ data }) => {
  if (!data || !data.transactions || data.transactions.length === 0) {
    return (
      <div className="transactions-card">
        <div className="transactions-header">
          <div className="transactions-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Transaction/List Icon */}
              <path d="M8 6h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 12h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 18h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 6h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 12h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 18h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="transactions-title">İşlem Geçmişi</div>
          <div className="transactions-info">
            {data.customer_id && (
              <span className="customer-id">Müşteri: {data.customer_id}</span>
            )}
            {data.account_id && (
              <span className="account-id">Hesap: {data.account_id}</span>
            )}
          </div>
        </div>
        <div className="transactions-empty">
          <p>İşlem bulunamadı</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionIcon = (amount) => {
    const numAmount = parseFloat(amount);
    if (numAmount > 0) {
      // Pozitif işlemler için sağ üst ok
      return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 7l-10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M17 17H7V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
    } else if (numAmount < 0) {
      // Negatif işlemler için sol alt ok
      return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M7 17l10-10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M7 7h10v10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
    } else {
      // Sıfır işlemler için yatay çizgi
      return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
    }
  };

  const getTransactionColor = (amount) => {
    const numAmount = parseFloat(amount);
    if (numAmount > 0) return 'positive';
    if (numAmount < 0) return 'negative';
    return 'neutral';
  };

  const isSingleItem = data.transactions.length === 1;

  return (
    <div className="transactions-card">
      <div className="transactions-header">
        <div className="transactions-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Transaction/List Icon */}
            <path d="M8 6h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 12h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 18h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 6h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 12h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 18h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="transactions-title">İşlem Geçmişi</div>
        <div className="transactions-info">
          {data.customer_id && (
            <span className="customer-id">Müşteri: {data.customer_id}</span>
          )}
          {data.account_id && (
            <span className="account-id">Hesap: {data.account_id}</span>
          )}
        </div>
      </div>
      
      <div className="transactions-content">
        <div className={`transactions-list ${isSingleItem ? 'single-item' : ''}`}>
          {data.transactions.map((transaction, index) => (
            <div key={transaction.transaction_id || index} className="transaction-item">
              <div className="transaction-header">
                <div className="transaction-left">
                  <div className="transaction-icon">
                    {getTransactionIcon(transaction.amount)}
                  </div>
                  <span className="transaction-description">
                    {transaction.description || 'İşlem'}
                  </span>
                </div>
                <span className={`transaction-amount ${getTransactionColor(transaction.amount)}`}>
                  {transaction.amount_formatted} {transaction.currency}
                </span>
              </div>
              
              <div className="transaction-content">
                <div className="transaction-meta">
                  <div className="transaction-meta-left">
                    <span className="transaction-date">
                      {formatDate(transaction.transaction_date)}
                    </span>
                    {transaction.balance_after && (
                      <span className="balance-after">
                        Bakiye: {parseFloat(transaction.balance_after).toLocaleString('tr-TR', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })} {transaction.currency}
                      </span>
                    )}
                  </div>
                  {transaction.type && (
                    <span className="transaction-type">
                      {transaction.type}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {data.transactions.length > 0 && (
          <div className="transactions-summary">
            {data.transactions.length} işlem gösteriliyor
          </div>
        )}
      </div>
    </div>
  );
};

export default TransactionsCard;
