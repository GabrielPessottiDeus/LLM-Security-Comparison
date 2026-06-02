package com.example.products;

import com.example.products.model.Product;
import com.example.products.repository.ProductRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.math.BigDecimal;

@SpringBootApplication
public class ProductsApplication {

    public static void main(String[] args) {
        SpringApplication.run(ProductsApplication.class, args);
    }

    @Bean
    CommandLineRunner seedDatabase(ProductRepository repository) {
        return args -> {
            if (repository.count() == 0) {
                repository.save(new Product("Notebook Dell Inspiron", "Notebook 15\" Intel Core i7, 16GB RAM, 512GB SSD", new BigDecimal("4599.90")));
                repository.save(new Product("Mouse Logitech MX Master 3", "Mouse sem fio ergonomico com scroll adaptativo", new BigDecimal("349.90")));
                repository.save(new Product("Teclado Mecanico Keychron K2", "Teclado mecanico compacto 75% com switches Brown", new BigDecimal("599.00")));
                repository.save(new Product("Monitor LG 27\" 4K", "Monitor IPS 27 polegadas resolucao 4K UHD HDR10", new BigDecimal("2199.00")));
                repository.save(new Product("Headset HyperX Cloud II", "Headset gamer com surround 7.1 e microfone removivel", new BigDecimal("449.90")));
            }
        };
    }
}
