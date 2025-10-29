$(document).ready(function () {
    const Toast = Swal.mixin({
        toast: true,
        position: "top",
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        },
    });

    const disabledButtons = ['credit-card', 'jazzcash', 'easypaisa'];

    disabledButtons.forEach(id => {
        $("#" + id).on("click", function(e) {
            e.preventDefault(); // Stop form submission
            Swal.fire({
                toast: true,
                position: 'top',
                icon: 'info',
                title: 'We are currently working on this payment method.',
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
            });
        });
    });

    function getCartId() {
    // Use consistent key: 'cart_id'
    let cartId = localStorage.getItem("cart_id");
    if (!cartId) {
        cartId = "";
        for (let i = 0; i < 10; i++) {
            cartId += Math.floor(Math.random() * 10);
        }
        localStorage.setItem("cart_id", cartId);
    }
    return cartId;
}

    $(document).on("click", ".add_to_cart", function () {
        const button_el = $(this);
        const id = button_el.attr("data-id");
        const qty = $(".quantity").val();
        const size = $("input[name='size']:checked").val() || null;
        const color = $("input[name='color']:checked").val() || null;
        const cart_id = getCartId();

        $.ajax({
            url: "/add_to_cart/",
            data: {
                id: id,
                quantity: qty,
                size: size,
                color: color,
                cart_id: cart_id,
            },
            beforeSend: function () {
                button_el.html('Adding To Cart <i class="fas fa-spinner fa-spin ms-2"></i>');
            },
            success: function (response) {
                console.log(response);
                Toast.fire({
                    icon: "success",
                    title: response.message,
                });
                button_el.html('Added To Cart <i class="fas fa-check-circle ms-2"></i>');
                $(".total_cart_items").text(response.total_cart_items);
            },
            error: function (xhr, status, error) {
                button_el.html('Add To Cart <i class="fas fa-shopping-cart ms-2"></i>');

                console.log("Error Status: " + xhr.status); // Logs the status code, e.g., 400
                console.log("Response Text: " + xhr.responseText); // Logs the actual response text (JSON string)

                // Try parsing the JSON response
                try {
                    let errorResponse = JSON.parse(xhr.responseText);
                    console.log("Error Message: " + errorResponse.error); // Logs "Missing required parameters"
                    Toast.fire({
                        icon: "error",
                        title: errorResponse.error,
                    });
                } catch (e) {
                    console.log("Could not parse JSON response");
                }

                // Optionally show an alert or display the error message in the UI
                console.log("Error: " + xhr.status + " - " + error);
            },
        });
    });

    $(document).on("click", ".update_cart_quantity", function () {
        const button_el = $(this);
        const update_type = button_el.attr("data-update_type");
        const product_id = button_el.attr("data-product_id");
        const item_id = button_el.attr("data-item_id");
        const cart_id = getCartId();
        var quantity = $(".item-quantity-" + item_id).val();

        if (update_type === "increase") {
            $(".item-quantity-" + item_id).val(parseInt(quantity) + 1);
            quantity++;
        } else {
            if (parseInt(quantity) <= 1) {
                $(".item-quantity-" + item_id).val(1);
                quantity = 1;
            } else {
                $(".item-quantity-" + item_id).val(parseInt(quantity) - 1);
                quantity--;
            }
        }

        $.ajax({
            url: "/add_to_cart/",
            data: {
                id: product_id,
                quantity: quantity,
                cart_id: cart_id,
            },
            beforeSend: function () {
                button_el.html('<i class="fas fa-spinner fa-spin"></i>');
            },
            success: function (response) {
                Toast.fire({
                    icon: "success",
                    title: response.message,
                });
                if (update_type === "increase") {
                    button_el.html("+");
                } else {
                    button_el.html("-");
                }
                $(".item_sub_total_" + item_id).text(response.item_sub_total);
                $(".cart_sub_total").text(response.cart_sub_total);
            },
            error: function (xhr, status, error) {
            console.log("Error Status: " + xhr.status);
            console.log("Response Text: " + xhr.responseText);
            try {
                let errorResponse = JSON.parse(xhr.responseText);
                console.log("Error Message: " + errorResponse.error);
                
                Toast.fire({
                    icon: "error",
                    title: errorResponse.error || "Something went wrong!"
                });
            } catch (e) {
                console.log("Could not parse JSON response");
                Toast.fire({
                    icon: "error",
                    title: "An unexpected error occurred."
                });
            }
        console.log("Error: " + xhr.status + " - " + error);
    },
});
});

    $(document).on("click", ".delete_cart_item", function () {
        const button_el = $(this);
        const item_id = button_el.attr("data-item_id");
        const product_id = button_el.attr("data-product_id");
        const cart_id = getCartId();

        $.ajax({
            url: "/delete_cart_item/",
            data: {
                id: product_id,
                item_id: item_id,
                cart_id: cart_id,
            },
            beforeSend: function () {
                button_el.html('<i class="fas fa-spinner fa-spin"></i>');
            },
            success: function (response) {
                Toast.fire({
                    icon: "success",
                    title: response.message,
                });
                $(".total_cart_items").text(response.total_cart_items);
                $(".cart_sub_total").text(response.cart_sub_total);
                $(".item_div_" + item_id).addClass("d-none");
            },
            error: function (xhr, status, error) {
                console.log("Error Status: " + xhr.status);
                console.log("Response Text: " + xhr.responseText);
                try {
                    let errorResponse = JSON.parse(xhr.responseText);
                    console.log("Error Message: " + errorResponse.error);
                    alert(errorResponse.error);
                } catch (e) {
                    console.log("Could not parse JSON response");
                }
                console.log("Error: " + xhr.status + " - " + error);
            },
        });
    });

    const fetchCountry = () => {
        fetch("https://api.ipregistry.co/?key=tryout")
            .then(function (response) {
                return response.json();
            })
            .then(function (payload) {
                console.log(payload.location.country.name + ", " + payload.location.city);
            });
    };
    fetchCountry();

    // Update the filter change event to handle search context better
    $(document).on('change', '.category-filter, .rating-filter, ' +
                'input[name="price-filter"], input[name="items-display"], ' +
                '.size-filter, .colors-filter', function () {

        // Get current search query from multiple possible sources
        let currentQuery = '';
        
        // Try to get from search input
        if ($('#searchFilter').length) {
            currentQuery = $('#searchFilter').val().trim();
        }
        
        // If empty, try to get from meta tag (for search page)
        if (!currentQuery && $('meta[name="current-query"]').length) {
            currentQuery = $('meta[name="current-query"]').attr('content') || '';
        }
        
        // If still empty, try to get from URL parameters (for search page)
        if (!currentQuery) {
            const urlParams = new URLSearchParams(window.location.search);
            currentQuery = urlParams.get('q') || '';
        }

        const filters = {
            categories : [],
            rating     : [],
            colors     : [],
            sizes      : [],
            prices     : '',
            display    : '',
            q          : currentQuery
        };

        $('.category-filter:checked').each(function () {
            filters.categories.push($(this).val());
        });
        $('.rating-filter:checked').each(function () {
            filters.rating.push($(this).val());
        });
        $('.size-filter:checked').each(function () {
            filters.sizes.push($(this).val());
        });
        $('.colors-filter:checked').each(function () {
            filters.colors.push($(this).val());
        });

        filters.display = $('input[name="items-display"]:checked').val() || '';
        filters.prices  = $('input[name="price-filter"]:checked').val()  || '';

        console.log('Sending filters:', filters); // Debug log

        $.ajax({
            url : '/filter_products/',
            data: $.param({
                'categories[]': filters.categories,
                'rating[]'    : filters.rating,
                'sizes[]'     : filters.sizes,
                'colors[]'    : filters.colors,
                'prices'      : filters.prices,
                'display'     : filters.display,
                'q'           : filters.q
            }, true),
            success: function (resp) {
                $('#products-list').html(resp.html);
                $('.product_count').text(resp.product_count);
            },
            error: function(xhr, status, error) {
                console.log('Filter error:', error);
            }
        });
    });

    // Update reset function to maintain search context
    $(document).on('click', '.reset_shop_filter_btn', function () {
        $('input[type=checkbox]').prop('checked', false);
        $('input[type=radio]').prop('checked', false);
        
        // Get current search query
        let currentQuery = '';
        if ($('#searchFilter').length) {
            currentQuery = $('#searchFilter').val().trim();
        }
        if (!currentQuery && $('meta[name="current-query"]').length) {
            currentQuery = $('meta[name="current-query"]').attr('content') || '';
        }
        if (!currentQuery) {
            const urlParams = new URLSearchParams(window.location.search);
            currentQuery = urlParams.get('q') || '';
        }
        
        $.ajax({
            url : '/filter_products/',
            data: { q: currentQuery },
            success: function (resp) {
                $('#products-list').html(resp.html);
                $('.product_count').text(resp.product_count);
            }
        });
    });

    $(document).on("click", ".add_to_wishlist", function () {
        const button = $(this);
        const product_id = button.attr("data-product_id");
        console.log(product_id);

        $.ajax({
            url: `/customer/add_to_wishlist/${product_id}/`,
            beforeSend: function () {
                button.html("<i class='fas fa-spinner fa-spin text-gray'></i>");
            },
            success: function (response) {
                button.html("<i class='fas fa-heart text-danger'></i>");
                console.log(response);
                if (response.message === "User is not logged in") {
                    button.html("<i class='fas fa-heart text-gray'></i>");

                    Toast.fire({
                        icon: "warning",
                        title: response.message,
                    });
                } else {
                    button.html("<i class='fas fa-heart text-danger'></i>");
                    Toast.fire({
                        icon: "success",
                        title: response.message,
                    });
                }
            },
        });
    });
});
