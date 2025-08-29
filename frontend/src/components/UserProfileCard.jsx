import React from 'react'
import './UserProfileCard.css'

const UserProfileCard = ({ userData }) => {
  if (!userData) {
    return (
      <div className="user-profile-card">
        <div className="profile-loading">Profil bilgileri yükleniyor...</div>
      </div>
    )
  }

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch (e) {
      return dateString
    }
  }

  return (
    <div className="user-profile-card">
      <div className="profile-header">
        <div className="profile-avatar">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="profile-title">
          <h3>Profil Bilgileri</h3>
        </div>
      </div>
      
      <div className="profile-content">
        <div className="profile-section">
          <h4>Kişisel Bilgiler</h4>
          <div className="profile-row">
            <span className="profile-label">Ad:</span>
            <span className="profile-value">{userData.name}</span>
          </div>
          <div className="profile-row">
            <span className="profile-label">Soyad:</span>
            <span className="profile-value">{userData.surname}</span>
          </div>
          <div className="profile-row">
            <span className="profile-label">E-posta:</span>
            <span className="profile-value">{userData.email}</span>
          </div>
          <div className="profile-row">
            <span className="profile-label">Telefon:</span>
            <span className="profile-value">{userData.phone}</span>
          </div>
        </div>

        <div className="profile-section">
          <h4>Hesap Bilgileri</h4>
          <div className="profile-row">
            <span className="profile-label">Müşteri ID:</span>
            <span className="profile-value">{userData.customer_id}</span>
          </div>
          <div className="profile-row">
            <span className="profile-label">Müşteri No:</span>
            <span className="profile-value">{userData.customer_no}</span>
          </div>
          <div className="profile-row">
            <span className="profile-label">Kayıt Tarihi:</span>
            <span className="profile-value">{formatDate(userData.created_at)}</span>
          </div>
        </div>

        <div className="profile-section">
          <h4>Adres Bilgileri</h4>
          <div className="profile-row">
            <span className="profile-label">Adres:</span>
            <span className="profile-value address">{userData.address}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserProfileCard
