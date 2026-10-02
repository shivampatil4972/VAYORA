package com.vayora.api.dto;

import com.vayora.api.model.RoleType;

import java.util.UUID;

public class JwtResponse {
    private String token;
    private String refreshToken;
    private String type = "Bearer";
    private UUID id;
    private String email;
    private String fullName;
    private RoleType role;

    public JwtResponse(String token, String refreshToken, UUID id, String email, String fullName, RoleType role) {
        this.token = token;
        this.refreshToken = refreshToken;
        this.id = id;
        this.email = email;
        this.fullName = fullName;
        this.role = role;
    }

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }

    public String getRefreshToken() { return refreshToken; }
    public void setRefreshToken(String refreshToken) { this.refreshToken = refreshToken; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public RoleType getRole() { return role; }
    public void setRole(RoleType role) { this.role = role; }
}
