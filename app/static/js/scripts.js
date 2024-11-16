 // this is the menu dropdown -->

document.addEventListener("DOMContentLoaded", function () {
    // Close the navbar when a dropdown item is clicked
    var dropdownItems = document.querySelectorAll('.dropdown-item');

    dropdownItems.forEach(function (item) {
        item.addEventListener('click', function () {
        // Close the navbar
        var navbarToggler = document.querySelector('.navbar-toggler');
        var navbarCollapse = document.querySelector('.navbar-collapse');

        if (navbarCollapse.classList.contains('show')) {
            navbarToggler.click(); // Trigger the toggler to close the navbar
        }

        // Remove active class from all dropdown items
        dropdownItems.forEach(function (el) {
            el.classList.remove('active');
        });

        // Add active class to the clicked dropdown item
        this.classList.add('active');
    });
});

// Change color of dropdown-toggle when dropdown is active
var dropdownToggles = document.querySelectorAll('.dropdown-toggle');

    dropdownToggles.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
        // Remove active class from all dropdown toggles
        dropdownToggles.forEach(function (el) {
            el.classList.remove('active');
        });

        // Add active class to the clicked dropdown toggle
        this.classList.add('active');
        });
    });
});


document.addEventListener('DOMContentLoaded', function () {
    const signupModalEl = document.getElementById('signupModal');
    const loginModalEl = document.getElementById('loginModal');

    // Function to show a modal
    function showModal(modalEl) {
    const modalInstance = new bootstrap.Modal(modalEl);
    modalInstance.show();
    }

    // Function to hide a modal
    function hideModal(modalEl) {
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) {
        modalInstance.hide();
    }
    }

    // Check for flash message and act accordingly
    const flashMessages = "{{ get_flashed_messages(category_filter=['success']) }}";

    if (flashMessages.includes('Signup successful!')) {
    hideModal(signupModalEl);

    setTimeout(function () {
        showModal(loginModalEl);
    }, 500);
    } else if (flashMessages.includes('Login successful!')) {
    hideModal(loginModalEl);

    // Update the admin button text to 'Logout' and clear the span text
    const adminBtn = document.querySelector('.admin__btn');
    adminBtn.textContent = 'Logout';
    adminBtn.querySelector('span').textContent = '';
    }

    // If you have buttons or links to switch between modals
    document.getElementById('switchToSignup').addEventListener('click', function () {
    hideModal(loginModalEl);
    showModal(signupModalEl);
    });

    document.getElementById('switchToLogin').addEventListener('click', function () {
    hideModal(signupModalEl);
    showModal(loginModalEl);
    });
});



// comfirmation Dialog for Deleting Partner
// Function to trigger the SweetAlert confirmation
function confirmPartnerDelete(partnerId) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit the form if confirmed
            document.getElementById(`deletePartnerForm-${partnerId}`).submit();
        }
    })
}


// comfirmation Dialog for Deleting portfolio
// Function to trigger the SweetAlert confirmation
function confirmDeletePortfolio(portfolio_id) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to undo this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit the form to delete the portfolio
            document.getElementById('deletePortfolioForm-' + portfolio_id).submit();
        }
    })
}



// comfirmation Dialog for Deleting portfolio images
// Function to trigger the SweetAlert confirmation
function confirmDeletePortfolioImage(portfolioId, mediaId) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'Do you want to delete this image?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            // Send an AJAX request to delete the image using the correct route
            fetch(`/portfolio/delete_image/${portfolioId}/${mediaId}`, {  // Adjusted to match the portfolio route
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token() }}',  // Ensure CSRF token is sent
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok || response.redirected) {
                    Swal.fire(
                        'Deleted!',
                        'The image has been deleted.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire(
                        'Error!',
                        'Something went wrong while deleting the image.',
                        'error'
                    );
                }
            })
            .catch(error => {
                Swal.fire(
                    'Error!',
                    `Something went wrong: ${error.message}`,
                    'error'
                );
                console.error('Error:', error);
            });
        }
    });
}




// comfirmation Dialog for Deleting CaseStudies
// Function to trigger the SweetAlert confirmation
function confirmDeleteCaseStudy(case_study_id) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to undo this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit the form to delete the portfolio
            document.getElementById('deleteCaseForm-' + case_study_id).submit();
        }
    })
}


// comfirmation Dialog for Deleting Case Studies images
// Function to trigger the SweetAlert confirmation
function confirmDeleteCaseImage(case_study_id, image_path) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'Do you want to delete this image?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            // Send an AJAX request to delete the image using the correct route
            fetch(`/casestudies/delete_image/${case_study_id}/${image_path}`, {  // Adjusted to match the portfolio route
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token() }}',  // Ensure CSRF token is sent
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok || response.redirected) {
                    Swal.fire(
                        'Deleted!',
                        'The image has been deleted.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire(
                        'Error!',
                        'Something went wrong while deleting the image.',
                        'error'
                    );
                }
            })
            .catch(error => {
                Swal.fire(
                    'Error!',
                    `Something went wrong: ${error.message}`,
                    'error'
                );
                console.error('Error:', error);
            });
        }
    });
}


// comfirmation Dialog for Deleting Blog 
// Function to trigger the SweetAlert confirmation
function confirmDeleteBlog(blog_id) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to undo this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit the form to delete the blog post
            document.getElementById('deleteBlogForm-' + blog_id).submit();
        }
    })
}


// comfirmation Dialog Deleting for Blog image  
// Function to trigger the SweetAlert confirmation
function deleteEditBlogImage(image_id, image_path) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'Do you want to delete this image?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            // Send image_id and image_path in the request body
            fetch(`/blogs/delete-edit-blog-image`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token() }}',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_id: image_id,
                    image_path: image_path
                })
            })
            .then(response => {
                if (response.ok || response.redirected) {
                    Swal.fire(
                        'Deleted!',
                        'The image has been deleted.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire(
                        'Error!',
                        'Something went wrong while deleting the image.',
                        'error'
                    );
                }
            })
            .catch(error => {
                Swal.fire(
                    'Error!',
                    `Something went wrong: ${error.message}`,
                    'error'
                );
                console.error('Error:', error);
            });
        }
    });
}





// comfirmation Dialog for Deleting Testimoial 
// Function to trigger the SweetAlert confirmation
function confirmDeleteTestimonial(form, testimonial_id) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to undo this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit the form directly
            form.submit();
        }
    })
}


document.addEventListener('DOMContentLoaded', function() {
    // Initialize SimpleMDE on the Add Blog modal textarea only once
    const addBlogTextarea = document.getElementById("blogContent");
    if (addBlogTextarea && !addBlogTextarea.classList.contains('simplemde-initialized')) {
        new SimpleMDE({ element: addBlogTextarea });
        addBlogTextarea.classList.add('simplemde-initialized'); // Mark as initialized
    }

    // Initialize SimpleMDE on each Edit Blog modal textarea when the modal is shown
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            const editTextarea = modal.querySelector("textarea.markdown-editor");

            if (editTextarea) {
                // Check if the editor has already been initialized for this textarea
                if (!editTextarea.classList.contains('simplemde-initialized')) {
                    // Initialize a new SimpleMDE instance and mark as initialized
                    const simplemde = new SimpleMDE({ element: editTextarea });
                    editTextarea.classList.add('simplemde-initialized');
                    
                    // Attach SimpleMDE instance to the textarea element
                    editTextarea.simplemde = simplemde;
                } else if (editTextarea.simplemde) {
                    // If already initialized, refresh content for the editor
                    editTextarea.simplemde.value(editTextarea.value);
                    editTextarea.simplemde.codemirror.refresh();
                }
            }
        });
    });
});


// Users Section
function confirmRemoveAdmin(url) {
    Swal.fire({
        title: "Are you sure?",
        text: "Do you really want to remove admin privileges?",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Yes, remove",
        cancelButtonText: "No",
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(url, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            title: "Success",
                            text: data.message,
                            icon: "success",
                        }).then(() => {
                            // Optionally, reload the page or navigate to a different URL
                            window.location.reload();
                        });
                    } else {
                        Swal.fire({
                            title: "Failed",
                            text: data.message,
                            icon: "error",
                        });
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    Swal.fire({
                        title: "Error",
                        text: "An error occurred. Please try again later.",
                        icon: "error",
                    });
                });
        }
    });
}





function confirmMakeAdmin(url) {
    Swal.fire({
        title: "Make this user an Admin?",
        text: "Are you sure you want to grant admin privileges?",
        icon: "info",
        showCancelButton: true,
        confirmButtonText: "Yes, make admin",
        cancelButtonText: "Cancel",
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(url, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            title: "Success",
                            text: data.message,
                            icon: "success",
                        }).then(() => {
                            // Optionally reload the page to reflect the changes
                            window.location.reload();
                        });
                    } else {
                        Swal.fire({
                            title: "Failed",
                            text: data.message,
                            icon: "error",
                        });
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    Swal.fire({
                        title: "Error",
                        text: "An error occurred. Please try again later.",
                        icon: "error",
                    });
                });
        }
    });
}





function confirmDeleteUser(url) {
    Swal.fire({
        title: "Are you sure?",
        text: "Once deleted, this user account cannot be recovered!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Yes, delete",
        cancelButtonText: "No",
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(url, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            title: "Success",
                            text: data.message,
                            icon: "success",
                        }).then(() => {
                            // Optionally reload the page to update user list
                            window.location.reload();
                        });
                    } else {
                        Swal.fire({
                            title: "Failed",
                            text: data.message,
                            icon: "error",
                        });
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    Swal.fire({
                        title: "Error",
                        text: "An error occurred. Please try again later.",
                        icon: "error",
                    });
                });
        }
    });
}


document.querySelectorAll('.markdown-content a').forEach(function (anchor) {
    anchor.setAttribute('target', '_blank');
});

var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            /* Toggle between adding and removing the "active" class,
            to highlight the button that controls the panel */
            this.classList.toggle("active");

            /* Toggle between hiding and showing the active panel */
            var panel = this.nextElementSibling;
            if (panel.style.display === "block") {
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
        }
    });
}


var swiper = new Swiper('.swiper-container', {
    effect: 'coverflow',
    grabCursor: true,
    centeredSlides: true,
    //slidesPerView: 3, // Shows 3 slides
    spaceBetween: 30, // Adds space between slides
    slidesPerView: 'auto',
    initialSlide: 2,
    coverflowEffect: {
        rotate: 0,
        stretch: 0,
        depth: 100,
        modifier: 2,
        slideShadows: false,
    },
    loop: true,
    pagination: {
        el: '.swiper-pagination',
        clickable: true, // Allows pagination dots to be clickable
    },
});


document.addEventListener("DOMContentLoaded", function () {
    // Manage all modals cleanup
    document.querySelectorAll('.modal').forEach(modalElement => {
        modalElement.addEventListener('hidden.bs.modal', function () {
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        });
    });

    // Testimonial modal handler
    const testimonialLinks = document.querySelectorAll('.testimonial-link');
    const testimonialModalElement = document.getElementById('testimonialModal');
    const testimonialModal = new bootstrap.Modal(testimonialModalElement);

    testimonialLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();

            const name = link.getAttribute('data-name');
            const title = link.getAttribute('data-title');
            const content = link.getAttribute('data-content');
            const imageUrl = link.getAttribute('data-image-url');

            document.getElementById('testimonialModalLabel').innerText = `${name} - ${title}`;
            document.getElementById('testimonialContent').innerText = content;
            document.getElementById('testimonialImage').src = imageUrl;

            testimonialModal.show();
        });
    });
});


$('#editTestimonialModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var id = button.data('id');
    var name = button.data('name');
    var title = button.data('title');
    var content = button.data('content');
    var imageUrl = button.data('image-url'); // Get the image URL from data attribute

    var modal = $(this);
    modal.find('#testimonialName').val(name);
    modal.find('#testimonialTitle').val(title);
    modal.find('#testimonialContent').val(content);
    modal.find('#testimonialImage').attr('src', imageUrl); // Set image dynamically
    modal.find('#testimonialId').val(id); // Hidden input for the ID if needed
});















