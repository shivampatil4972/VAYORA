package com.vayora.api.service;

import com.vayora.api.dto.JwtResponse;
import com.vayora.api.dto.LoginRequest;
import com.vayora.api.dto.RegisterRequest;
import com.vayora.api.dto.TokenRefreshRequest;
import com.vayora.api.dto.TokenRefreshResponse;
import com.vayora.api.model.Driver;
import com.vayora.api.model.Passenger;
import com.vayora.api.model.RoleType;
import com.vayora.api.model.User;
import com.vayora.api.repository.DriverRepository;
import com.vayora.api.repository.PassengerRepository;
import com.vayora.api.repository.UserRepository;
import com.vayora.api.security.jwt.JwtUtils;
import com.vayora.api.security.services.UserDetailsImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Service
public class AuthService {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PassengerRepository passengerRepository;

    @Autowired
    private DriverRepository driverRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtils jwtUtils;

    @Value("${vayora.jwt.refresh-token-expiry-ms}")
    private Long refreshTokenDurationMs;

    @Transactional
    public void registerUser(RegisterRequest registerRequest) {
        if (userRepository.existsByEmail(registerRequest.getEmail())) {
            throw new RuntimeException("Error: Email is already in use!");
        }

        User user = new User();
        user.setFullName(registerRequest.getFullName());
        user.setEmail(registerRequest.getEmail());
        user.setPasswordHash(passwordEncoder.encode(registerRequest.getPassword()));
        user.setPhone(registerRequest.getPhone());
        user.setRole(registerRequest.getRole());

        user = userRepository.save(user);

        if (registerRequest.getRole() == RoleType.PASSENGER) {
            Passenger passenger = new Passenger();
            passenger.setId(user.getId());
            passengerRepository.save(passenger);
        } else if (registerRequest.getRole() == RoleType.DRIVER) {
            Driver driver = new Driver();
            driver.setId(user.getId());
            driverRepository.save(driver);
        }
    }

    @Transactional
    public JwtResponse authenticateUser(LoginRequest loginRequest) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(loginRequest.getEmail(), loginRequest.getPassword()));

        SecurityContextHolder.getContext().setAuthentication(authentication);
        String jwt = jwtUtils.generateJwtToken(authentication);

        UserDetailsImpl userDetails = (UserDetailsImpl) authentication.getPrincipal();

        User user = userRepository.findById(userDetails.getId()).orElseThrow();

        String refreshToken = UUID.randomUUID().toString();
        user.setRefreshToken(refreshToken);
        user.setRefreshTokenExpiry(Instant.now().plusMillis(refreshTokenDurationMs));
        userRepository.save(user);

        return new JwtResponse(jwt, refreshToken, user.getId(), user.getEmail(), user.getFullName(), user.getRole());
    }

    @Transactional
    public TokenRefreshResponse refreshToken(TokenRefreshRequest request) {
        String requestRefreshToken = request.getRefreshToken();

        User user = userRepository.findByRefreshToken(requestRefreshToken)
                .orElseThrow(() -> new RuntimeException("Refresh token is not in database!"));

        if (user.getRefreshTokenExpiry().compareTo(Instant.now()) < 0) {
            userRepository.save(user);
            throw new RuntimeException("Refresh token was expired. Please make a new signin request");
        }

        String token = jwtUtils.generateTokenFromUsername(user.getEmail());

        return new TokenRefreshResponse(token, requestRefreshToken);
    }
}
