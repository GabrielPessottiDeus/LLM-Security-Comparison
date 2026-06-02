package com.example.products.config;

import com.example.products.entity.Product;
import com.example.products.repository.ProductRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

@Component
public class DataInitializer implements CommandLineRunner {

    private final ProductRepository productRepository;

    public DataInitializer(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @Override
    public void run(String... args) {
        if (productRepository.count() > 0) {
            return;
        }

        productRepository.save(new Product("Notebook Pro 14", "Notebook com 16GB RAM e SSD de 512GB", new BigDecimal("6999.90")));
        productRepository.save(new Product("Mouse Gamer X", "Mouse óptico com 6 botões programáveis", new BigDecimal("189.90")));
        productRepository.save(new Product("Teclado Mecânico K68", "Teclado mecânico ABNT2 com switch blue", new BigDecimal("349.90")));
        productRepository.save(new Product("Monitor UltraWide 29", "Monitor 29 polegadas IPS Full HD", new BigDecimal("1299.00")));
        productRepository.save(new Product("Headset Studio H1", "Headset com cancelamento de ruído", new BigDecimal("459.50")));
    }
}
