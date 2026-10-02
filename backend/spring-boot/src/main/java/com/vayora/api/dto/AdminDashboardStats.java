package com.vayora.api.dto;

import java.util.Map;

public class AdminDashboardStats {
    private long totalUsers;
    private long totalDrivers;
    private long totalPassengers;
    private long totalRides;
    private long activeRides;
    private long totalBookings;
    
    // Extensibility for AI/KPI metrics
    private Map<String, Object> aiMetrics;

    public long getTotalUsers() { return totalUsers; }
    public void setTotalUsers(long totalUsers) { this.totalUsers = totalUsers; }

    public long getTotalDrivers() { return totalDrivers; }
    public void setTotalDrivers(long totalDrivers) { this.totalDrivers = totalDrivers; }

    public long getTotalPassengers() { return totalPassengers; }
    public void setTotalPassengers(long totalPassengers) { this.totalPassengers = totalPassengers; }

    public long getTotalRides() { return totalRides; }
    public void setTotalRides(long totalRides) { this.totalRides = totalRides; }

    public long getActiveRides() { return activeRides; }
    public void setActiveRides(long activeRides) { this.activeRides = activeRides; }

    public long getTotalBookings() { return totalBookings; }
    public void setTotalBookings(long totalBookings) { this.totalBookings = totalBookings; }

    public Map<String, Object> getAiMetrics() { return aiMetrics; }
    public void setAiMetrics(Map<String, Object> aiMetrics) { this.aiMetrics = aiMetrics; }
}
