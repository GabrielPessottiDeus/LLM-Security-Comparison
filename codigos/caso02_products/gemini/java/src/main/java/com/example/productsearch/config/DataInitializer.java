package com.example.productsearch.config;

import com.example.productsearch.model.Product;
import com.example.productsearch.repository.ProductRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.List;

@Component
public class DataInitializer implements CommandLineRunner {

    private final ProductRepository productRepository;

    public DataInitializer(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @Override
    public void run(String... args) {
        if (productRepository.count() == 0) {
            productRepository.saveAll(List.of(
                    new Product("Smartphone Galaxy Z", "Smartphone dobrável com 256GB", new BigDecimal("5999.99")),
                    new Product("Notebook Pro", "Notebook 16GB RAM e 512GB SSD", new BigDecimal("4500.50")),
                    new Product("Monitor UltraWide", "Monitor 29 polegadas IPS", new BigDecimal("1200.00")),
                    new Product("Teclado Mecânico RGB", "Teclado mecânico switch brown", new BigDecimal("350.00")),
                    new Product("Mouse Sem Fio", "Mouse ergonômico bluetooth", new BigDecimal("150.75"))
            ));
        }
    }
}