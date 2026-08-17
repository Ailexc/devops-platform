// Package auth JWT + OAuth Client Credentials（程序身份签发）
package auth

import (
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var ErrInvalidToken = errors.New("invalid token")

// Claims 统一 JWT 载荷
// sub 格式：u:{user_id}（用户） / client:{client_id}（程序身份）
type Claims struct {
	SubjectType int16  `json:"st"` // 1=user 2=service
	SubjectKey  string `json:"sk"` // 决策主体 key（u:alice / s:cloud-mgmt）
	Username    string `json:"un"`
	TokenVer    int    `json:"tv"` // 用户 token_version（即时失效）
	Scope       string `json:"scope,omitempty"`
	AppID       uint64 `json:"app_id,omitempty"`
	TokenType   string `json:"tt"` // access / refresh / scoped
	TTLSeconds  int64  `json:"ttl,omitempty"`
	jwt.RegisteredClaims
}

type Manager struct {
	secret     []byte
	accessTTL  time.Duration
	refreshTTL time.Duration
}

func NewManager(secret string, accessTTL, refreshTTL time.Duration) *Manager {
	return &Manager{secret: []byte(secret), accessTTL: accessTTL, refreshTTL: refreshTTL}
}

func (m *Manager) Sign(claims *Claims) (string, error) {
	claims.RegisteredClaims = jwt.RegisteredClaims{
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		ExpiresAt: jwt.NewNumericDate(time.Now().Add(m.accessTTL)),
		Issuer:    "iam",
	}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(m.secret)
}

func (m *Manager) SignWithTTL(claims *Claims, ttl time.Duration) (string, error) {
	claims.RegisteredClaims = jwt.RegisteredClaims{
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		ExpiresAt: jwt.NewNumericDate(time.Now().Add(ttl)),
		Issuer:    "iam",
	}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(m.secret)
}

func (m *Manager) Parse(token string) (*Claims, error) {
	c := &Claims{}
	_, err := jwt.ParseWithClaims(token, c, func(t *jwt.Token) (any, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, ErrInvalidToken
		}
		return m.secret, nil
	})
	if err != nil {
		return nil, err
	}
	return c, nil
}

func (m *Manager) AccessTTL() time.Duration  { return m.accessTTL }
func (m *Manager) RefreshTTL() time.Duration { return m.refreshTTL }
