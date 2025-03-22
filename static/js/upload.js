document.addEventListener('DOMContentLoaded', function() {
    const imgArea = document.querySelector('.img-area');
    const inputFile = document.getElementById('file-upload');

    imgArea.addEventListener('click', function () {
        inputFile.click();
    });

    inputFile.addEventListener('change', function () {
        const image = this.files[0];
        if (image) {
            if (image.size < 2000000) {
                const reader = new FileReader();
                reader.onload = function () {
                    const allImg = imgArea.querySelectorAll('img');
                    allImg.forEach(item => item.remove());
                    const imgUrl = reader.result;
                    const img = document.createElement('img');
                    img.src = imgUrl;
                    imgArea.appendChild(img);
                    imgArea.classList.add('active');
                    imgArea.dataset.img = image.name;
                };
                reader.readAsDataURL(image);
            } else {
                alert("Image size more than 2MB");
            }
        }
    });
});
