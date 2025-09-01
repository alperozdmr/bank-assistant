import './BalanceCard.css'
import { useState } from 'react'
import { createPortal } from 'react-dom'

const InfoButton = ({ onClick, className = '' }) => (
  <button
    className={`account-info-btn ${className}`.trim()}
    onClick={(e) => { e.stopPropagation(); onClick(); }}
    title="Detay"
    aria-label="Hesap detayı"
  >
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
      <path d="M12 10v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M12 7h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  </button>
)

const BalanceCard = ({ cardData }) => {
  const [selectedAccount, setSelectedAccount] = useState(null)
  if (!cardData || cardData.type !== 'balance_card') return null

  if (cardData.card_type === 'single_account') {
    const acc = {
      account_id: cardData.account_id,
      customer_id: cardData.customer_id,
      account_number: cardData.account_number,
      iban: cardData.iban,
      account_type: cardData.account_type,
      status: cardData.status,
      balance: cardData.balance,
      currency: cardData.currency,
      created_at: cardData.created_at,
    }
    return (
      <div className="balance-card">
                 <div className="balance-card-header">
           <div className="balance-card-icon">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
               {/* Wallet Icon */}
               <rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
               <rect x="3" y="8" width="18" height="8" rx="1" fill="currentColor" opacity="0.1"/>
               <rect x="17" y="10" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
               <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
             </svg>
           </div>
           <div className="balance-card-title">Hesap Bakiyesi</div>
         </div>
        <div className="balance-card-content">
          <div className="account-info">
            <div className="account-id">Hesap No: {cardData.account_id}</div>
            <div className="account-details">
              <div className="account-type">
                <span className="label">Hesap Türü:</span>
                <span className="value">{cardData.account_type}</span>
              </div>
              <div className="account-status">
                <span className="label">Durum:</span>
                <span className={`status-badge ${cardData.status?.toLowerCase()}`}>
                  {cardData.status}
                </span>
              </div>
            </div>
            {(acc.iban || acc.account_number) && (
              <div className="account-iban">
                <span className="label">IBAN:</span>
                <span className="value">{acc.iban || acc.account_number}</span>
              </div>
            )}
          </div>
          <div className="balance-amount">
            <span className="amount">{cardData.balance}</span>
            <span className="currency">{cardData.currency}</span>
          </div>
        </div>
      </div>
    )
  }

  if (cardData.card_type === 'multiple_accounts') {
    return (
      <div className="balance-card">
                 <div className="balance-card-header">
           <div className="balance-card-icon">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
               {/* Wallet Icon */}
               <rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
               <rect x="3" y="8" width="18" height="8" rx="1" fill="currentColor" opacity="0.1"/>
               <rect x="17" y="10" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
               <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
             </svg>
           </div>
           <div className="balance-card-title">Hesap Bakiyeleri</div>
         </div>
        <div className="balance-card-content">
          <div className="accounts-list">
            {cardData.accounts.map((account, index) => (
              <div key={index} className="account-item">
                <div className="account-info">
                  <div className="account-id">Hesap {account.account_id}</div>
                  <div className="account-meta">
                    <span className="account-type-small">{account.account_type}</span>
                    <span className={`status-badge-small ${account.status?.toLowerCase()}`}>
                      {account.status}
                    </span>
                  </div>
                  {(account.iban || account.account_number) && (
                    <div className="account-iban-small">
                      <span className="label">IBAN:</span>
                      <span className="value">{account.iban || account.account_number}</span>
                    </div>
                  )}
                </div>
                <div className="account-balance">
                  <span className="amount">{account.balance}</span>
                  <span className="currency">{account.currency}</span>
                </div>
              </div>
            ))}
          </div>
          {cardData.total_count > 0 && (
            <div className="balance-summary">
              {cardData.total_count} hesap gösteriliyor
            </div>
          )}
        </div>
      </div>
    )
  }



  return null
}

export default BalanceCard
